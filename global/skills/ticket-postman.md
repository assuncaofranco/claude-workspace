---
description: Generate a Postman collection that drives a ticket's full end-to-end flow through the product's real entry points, so it can be run by hand — including by the PO in a shared pre-production environment. Pass the ticket id as argument.
argument-hint: <TICKET or short slug>
---

# ticket-postman

Generate a Postman v2.1 collection that exercises a ticket's **whole flow end-to-end** through the
real **entry points** — the admin API and the player API — so the ticket can be validated by hand.
Invoke as `/ticket-postman <TICKET>`.

Project-specific endpoints, ports, path conventions and the canonical reference chain live in the
project's own context (for Celesta: `celesta-microservices/context.yaml` and
`celesta-microservices/postman-reference.md`). Credentials live in `~/.claude-secrets/`, never here
and never in the collection file.

## Golden rule — drive from the entry points

Prefer the admin and player entry points for every step. **Avoid calling internal services
directly** — they aren't reachable from a shared pre-production environment, so a collection that
depends on them can't be run by the PO. Only hit an internal service when a step has no entry-point
equivalent (a provider callback, say); mark it **DEV-ONLY** and sign it with whatever inter-service
header the project uses. If the whole ticket can only be exercised through internal calls, say so
explicitly in the output.

## Steps

1. **Identify the ticket and its flow.**
   - Take the ticket id from `$ARGUMENTS`; if absent, ask.
   - Read the ticket's spec and plan where the project's SDD keeps them (overlay) to learn what changes, which entry points
     it uses and which endpoints it exercises. If there is no spec, ask for the flow in one or two
     sentences.
   - **The ticket's variation matrix (`ticket-matrix`, `matrix.md` in the ticket's folder) is the run list.** One run per A-cell, each
     asserting that cell's acceptance criterion — not one happy path plus a note that the other
     variants "should behave the same". If a cell's criterion can't be asserted through the entry
     points, say so **now**: it can't be verified in pre-production either, and that is worth knowing
     before the code is written.

2. **Map the ordered endpoint chain, entry-point first.**
   - **Generate the API spec first — it is not committed.** Run the project's doc target
     (`make openapi` or equivalent). For each request take the exact method, path, body and params
     from that generated spec plus the controller's route/schema attributes. **Never invent** a
     field, a param or an endpoint.
   - **Build from the docs on purpose.** Anything the ticket did *not* create is already documented —
     take it from the spec, not from reading code. Anything the ticket *does* create isn't in the
     spec yet (annotations only produce output once the code exists), so that part comes from the
     ticket's own plan and gets verified in step 6.

3. **Inspect existing data; decide what to create.**
   - Use `db-query` to find real ids. Column names aren't guessable — discover them from
     `information_schema` before writing a query against them.
   - Confirm prerequisites exist and grab real ids. Reuse existing rows; create (through the admin
     API) only what the ticket needs and is missing.

4. **Build the collection.**
   - **Variables** — base URLs plus an empty var for every captured id. Credentials are **referenced
     from the vault at run time**, never written into the file.
   - **Auth folder** — the token requests, each with a post-response script that saves the token into
     its variable and asserts 200.
   - **Flow folders grouped by actor/token**, each actor's token request at the top of its folder, so
     a token isn't fetched long before use and then expires.
   - **DEV-ONLY folder**, only if unavoidable, for direct internal calls.
   - **Verify** — prefer an entry-point read; a direct internal read is DEV-ONLY.

5. **Save and document.**
   - **No ticket yet** (ad-hoc investigation, bug repro before a ticket exists): don't block on asking
     for an id — use a short descriptive slug and save outside every service repo, in the local
     collections folder named by the project context. That folder exists so an ad-hoc collection
     can't be committed by accident. Once a real ticket exists, move both files into that ticket's
     folder (below). In this mode the "test the FEATURE, not the bug" rule below does **not**
     apply — reproducing the bug can be the entire point; say so in the Notes.
   - **Has a ticket:** write the collection into the ticket's folder on our side (overlay), never into
     a service repo. The collection is our tool, not a team artifact (`rules/deliverables.md`).
   - Write a `<TICKET>.md` beside it — **terse runbook for a human, not a report.** No justification
     paragraphs, no "verified by hand" narration, no bug write-up woven into the steps. Fixed
     sections, in this order: title; `**Feature:**` one line; `## Setup` (2-4 bullets: import, bring
     up containers, run order); `## Steps` (numbered, one short phrase each, no explanation of why);
     `## Variables` (table `Variable | Example | What it is`, plus one line naming what's captured at
     runtime); `## Notes` (bullets only — PO-runnable vs DEV-only split, gotchas, expected result; a
     bug found along the way gets ONE bullet, not a subsection).

6. **Run it yourself, then cross-check the three sides.**
   You always run the collection before handing it over, so you always hold the real response bodies.
   **Run it with Newman**, not by eyeballing the JSON or single-stepping by hand — a collection can
   look correct and still fail for reasons inspection won't catch: a pre-request script throwing, a
   signature computed over an unresolved `{{variable}}` that then mismatches the resolved body, a
   path accessor returning a string where the script expects an array. All three have actually
   happened. They surface as silent 403/404s, not as anything visible in the file. Fix until Newman
   reports 0 failures.

   Newman can't validate a step that needs a human in the loop (a console command between two
   requests, a step gated on real time passing) — those still need a manual pass, but every pure-HTTP
   chain runs clean under Newman first.

   Then **regenerate the spec** (step 2) — the annotations for whatever the ticket added only produce
   output once the code is there. Then compare:
   - **Request rejected?** The body was built from the docs, so a 400 means docs and code disagree.
   - **Response shape vs. documented response schema.** Both directions are bugs: a documented field
     that never appears, and a returned field that isn't documented. Neither shows up in the
     collection itself — the collection only knows which endpoints to call — so this comparison is
     the only thing that catches them.

7. **Diagnose a divergence — don't assume who is wrong.**
   - **Pre-existing code** (anything the ticket didn't touch): the framework's own request-validation
     object (in Symfony, the Form Type) is the source of truth. It's external, it shipped before this
     ticket, it decides. If the docs disagree with it, the docs are the bug.
   - **Code this ticket created:** nothing is authoritative. The spec, the plan, the code, the
     annotation and the collection were all produced by us in this ticket, so a mismatch proves only
     that we got something wrong somewhere — not which one. Investigate against the business need
     established in `ticket-understand`. Amending the spec or plan mid-ticket is a legitimate
     outcome, not a process failure. Never close the question with "it's specified".
   - Fix the annotation as part of the ticket when the wrong doc is on code this ticket touched. If
     it's pre-existing and unrelated, report it and leave it alone.

## Newman

Install once per machine if missing (`which newman || npm install -g newman`). A
`newman: command not found` right after installing is a PATH problem, not a missing binary — check
the npm prefix and prepend its `bin`.

```bash
newman run <collection>.json                            # whole thing, in file order
newman run <collection>.json --folder "<folder name>"   # one folder
```

Folders run in **separate** invocations do **not** share captured variables — a var set in one run is
gone in the next. To test a folder that depends on an earlier capture without re-running everything,
pass the value in with `--env-var "key=value"`. A real end-to-end pass is the full collection in one
invocation.

A clean pass is `failed: 0` on **every** row of the summary — iterations, requests, test-scripts,
prerequest-scripts, assertions. A script `ReferenceError`/`TypeError` shows up as a script-row
failure with a stack trace, not as an unexpected HTTP status, so check that row even when every
request shows 200.

## Rules

- **Entry-point first.** Direct internal calls are DEV-ONLY, signed, and flagged as not-PO-runnable.
- Request shapes come from the generated API spec and the controller attributes — never invented.
- Capture tokens and ids into variables via post-response scripts and chain them; the collection is
  order-dependent, and the run instructions must say so.
- Capture a chained id **in the same actor block that uses it**. Don't assemble a value out of
  variables set in a different block — it works locally and breaks across environments. Prefer
  reading an id straight from a list response over rebuilding it.
- Discover real ids and columns before hardcoding; reuse existing rows, create only what's missing.
- Test the FEATURE (happy path). Don't add steps whose only purpose is to reproduce the bug —
  except in the ad-hoc no-ticket mode of step 5.
- Make the collection **self-contained**: define every variable in the collection with dev defaults
  and have captures write to collection variables, so it runs with **No environment**. Don't ship an
  environment file by default. A per-stage environment carries only config vars (URLs, ids) —
  **never** the captured/token vars, or the selected environment shadows the collection's own
  captures. **And never credentials**: those come from the vault into the runner's environment at run
  time, so the committed file has nothing to leak.
- Keep it minimal: the requests the feature needs, plus auth and one verification read.

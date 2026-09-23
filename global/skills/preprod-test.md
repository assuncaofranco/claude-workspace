---
description: Verify an already-deployed fix or feature directly in a shared pre-production environment, driving only through the public entry points — never touching internal services, the database, or another test's data.
argument-hint: <TICKET or brief description of what to verify>
---

# preprod-test

Verifies `$ARGUMENTS` in the shared pre-production environment. Not a replacement for `ticket-test`
(which builds the local scenario) — this is the final, real-environment check, and it has a different
set of constraints because the environment is shared and largely off-limits below the API layer.

## Credentials come from the vault, never from this file

Environment credentials live in `~/.claude-secrets/`, outside any git tree. Read the file named by
`secrets:` in the project's context table (for Celesta: `celesta-microservices/context.yaml` →
`secrets.preprod`), load the values into the environment of whatever drives the requests, and **never
write them back** into a skill, a spec, a plan, a versioned collection, an Artifact, a PR comment or
a chat log that gets shared.

If the vault has no entry for the environment or brand under test, stop and ask. Do not substitute a
credential from a different brand because it happens to authenticate — see the brand rule below.

## Before anything: confirm the deploy

Pre-production does not necessarily have the change yet. Ask the user whether the branch/PR under
test is already deployed there. If it isn't, stop — there is nothing to verify until it is.

## Entry points only

Same golden rule as `ticket-postman`: drive everything through the **admin** and **player** entry
points, connected to the VPN. Never call an internal service directly.

No signature-header shortcuts. Those are local-dev tricks to bypass gateway auth against the docker
containers; here there is no equivalent. Go through the real screens and endpoints a user or an admin
would actually use.

If a step genuinely has no entry-point equivalent (a provider webhook, say), say so explicitly
instead of improvising a direct call to the internal service.

## Brand is discovered, not assumed

Different brands use different OAuth clients, and the default brand in the vault is a default, not a
universal. A player of one vertical does not exist under another vertical's domain.

Discover the right one — list the active domains, then fetch the player under a candidate domain and
expect a 404 until it matches — rather than assuming. The shared credential can usually **read**
every domain; a per-brand credential is only needed to **write**. If the ticket touches a brand whose
credential isn't in the vault, ask for it before assuming.

## No database access here

This skill assumes no bastion, no SSH, no DB client. If something has to be confirmed at the database
or at any infra level the API response doesn't surface, **ask the user to run the check and report
back** — don't reach for direct access yourself.

## Shared environment — read or create, never alter

Other people's test data and in-flight work live in the same environment. Default to:

- **Read** existing state through the entry points to understand it.
- **Create** new, clearly-named test data to exercise the flow.
- **Never** update, disable or clean up something you didn't create to get a convenient test window.
  No bulk-disabling other configs, no touching another player's state. If leftover state is in the
  way, ask before touching it — it may not be yours to clear.

Name anything created with the ticket id (`<TICKET> - test config`) so it's identifiable and safe for
others to ignore.

## No forced timing

Techniques that only work by editing source — a sleep inserted to reproduce a race locally — don't
apply here, because that source isn't deployed. Observe behaviour as it naturally occurs; don't try
to manufacture a race.

## Coverage — the matrix decides, not the happy path

This step exists because tickets came back rejected for partial implementations: correct on the
variant we drove, silently wrong on the ones we never ran. So the run is not "does it work" — it is
**every A-cell of the ticket's variation matrix** (`ticket-matrix`, carried in the spec's acceptance
criteria), each asserted against its own acceptance criterion.

- One run per A-cell. A criterion that can't be observed through the entry points can't be verified
  here — say so explicitly instead of declaring it passed.
- **Invent nothing.** A case that isn't in the matrix doesn't get tested on a hunch; it gets added to
  the matrix first, which is also how we find out the enumeration was incomplete.
- **Partial coverage is a result, not a footnote.** If only 4 of 7 A-cells could be driven, report
  4 of 7 and name the 3, before saying anything about whether it works.

## Steps

1. Confirm the change is deployed (ask, don't assume).
2. Confirm the brand/domain — discover it; ask for credentials if the ticket's brand needs different
   ones than the vault holds.
3. Pull the A-cells and their acceptance criteria from the ticket's spec. That list **is** the test
   plan — if the ticket has no matrix, stop and build one before testing.
4. Identify the entry-point calls that exercise each cell. Reuse the ticket's Postman collection
   (`ticket-postman`) if one exists and already targets these entry points — its runs should already
   be the A-cells.
5. Create whatever test data is needed through the entry points, named with the ticket id.
6. Drive each cell, observing real timing and real responses — no artificial delays, no internal
   shortcuts.
7. For anything not visible in the API response, ask the user to check and report.
8. Report cell by cell against its acceptance criterion, citing the actual response or the
   user-reported state. A summary line ("tudo ok") without the per-cell result defeats the step.

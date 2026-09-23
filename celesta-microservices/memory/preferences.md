---
name: preferences
description: "Standing collaboration/communication rules for this user — apply always, not tied to any one step of the ticket workflow"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 58764f81-09fb-467a-bc18-586ea7655178
  modified: 2026-08-31T09:10:38.865Z
---

## Terse, human communication
Never say more than necessary. No AI-verbose padding — no restating what was just done, no filler summaries, no trailing recap nobody asked for.

**Why:** explicit standing instruction from the user during a CLS-1639 review session: "Most important rule in our conversation: never say too much. no ai verbose stuff... In our conversation, say only the necessary. human conversation, pls."

**How to apply:** keep responses short and direct across all conversation, not just reviews. Give findings/answers plainly (short bullet or table). When debating a design or a decision (e.g. reorganizing memory/skills), go back and forth in short exchanges — one idea or question at a time — instead of dumping the full picture in one message; details belong in a plan file or the eventual deliverable, not the chat.

## Give a genuine opinion, don't rubber-stamp
When the user proposes a categorization, an organization, or a design choice, evaluate it for real — agree or disagree based on what's actually best (e.g. for how cheaply/reliably Claude itself can reach the information later), not because the user suggested it.

**Why:** said explicitly during the memory/skills reorganization — the whole point of reorganizing is for Claude to reach information fast and cheaply; automatic agreement defeats that purpose.

**How to apply:** especially during any design/organization discussion, state a real independent judgment, including disagreement, before executing.

## Reviewing code: verify live git state, never lean on the plan/conversation

When asked to review a diff (`ticket-review` or ad hoc), re-derive everything from `git status`/`git diff` against the actual current branch state — even if the same conversation already planned and discussed every change in detail.

**Why:** said explicitly during CLS-1285-CLS-2391 review ("vc e soh o reviewer, nao quero que use memoria pra fazer review"). Implementation drifts from what was planned/discussed — that drift is exactly what a review exists to catch. Concretely caught this way in that session: a `composer.json`/`composer.lock` pointing at an ungitignored local `path` repository that no plan or description had mentioned.

**How to apply:** for every repo touched, run `git status`/`git diff master` fresh before commenting — do not summarize from what was said earlier about "what the fix does."

## No AI-tells in reviewed deliverables — code, comments, and generated docs

**Why:** said explicitly during the same review ("Nao permita comentarios de IA. Nao permita verbosidade, mesmo tecnica, de IA"). Applies beyond chat responses (already covered above) to anything Claude is asked to review: flag AI-style comments added to code, and in SDD-style spec/plan docs, flag template sections filled in just to say "N/A"/"None" — don't pad a document to look complete, and don't approve one that does.

**How to apply:** when reviewing a diff or a spec/plan doc, explicitly check for and call out (a) comments added to the code that a human wouldn't have bothered writing, (b) template sections answered only with "none"/"not applicable" that could simply be omitted.

## Cite the coding-standards.md path when flagging a standards violation in a review

When a review finding cites a forbidden-function/style rule, name the real source: `vendor/lancasters/celesta-dev/config/phpinsights.php`, class `CelestaDev\OverWrites\ForbiddenFunctionsSniffCelesta` (`forbiddenFunctions` array) — not just "the coding standard."

**Why:** asked explicitly during the CLS-1069 flock review (Marcello's PR) after finding `is_resource()` was forbidden — the user wanted the source traceable, not just asserted, and then clarified the real celesta-dev path should be the one cited, not our cached copy.

**How to apply:** `lancasters/celesta-dev` is our own library, source at `git@github.com:celesta-tech/celesta-dev.git`, published as a private composer package (repo.packagist.com/lancastersolutions) and pulled into each service's own `vendor/`. Cloned locally (2026-08-31) at `/Users/l.franco/Desktop/celesta-projects/celesta-dev/` — cite `celesta-dev/config/phpinsights.php` (class `CelestaDev\OverWrites\ForbiddenFunctionsSniffCelesta`) as the canonical source in reviews, not a per-service vendor copy (those are pinned to whatever version.composer.lock resolved, could lag the repo). Confirmed (2026-08-31) the package is installed via vendor/ in celesta-backoffice, celesta-segment, celesta-fraud, celesta-cms, celesta-scenario, celesta-contact, celesta-promotion, celesta-wallet, celesta-statistics, celesta-gateway, celesta-game, celesta-crm, celesta-payment — NOT in celesta-scripts (no phpinsights/lint CI there at all), so a celesta-scripts review cites the celesta-dev repo directly rather than any local vendor path. `~/.claude/shared/coding-standards.md` stays our cache for quick lookups without opening the repo; trust it for our own checks, but cite the real `celesta-dev` path in review comments.

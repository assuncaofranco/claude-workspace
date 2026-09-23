---
description: Write the fix/feature for a ticket, after ticket-understand and ticket-test have already run. Applies Celesta's coding constraints at generation time, not after the fact.
argument-hint: <TICKET>
---

# ticket-code

Write the code for `$ARGUMENTS`. Assumes `ticket-understand` already produced the business-logic understanding and `ticket-test` already produced (or updated) the Postman scenario used to drive/verify it. Do not start this step from a bare ticket description alone.

## Rules — apply these while writing, don't wait for review to catch them

**The matrix's A-cells are the scope, all of them.** Every cell `ticket-matrix` marked affected is a requirement, not an edge case — an A-cell with no code path is an unfinished ticket, and "it works for the main type" is exactly the partial implementation that gets tickets rejected. If, while writing, a cell turns out to need something the plan didn't account for, say so instead of quietly implementing the subset that was easy.

**Never touch lines you don't need to.** Change only what the ticket requires. Do not run a whole-file formatter/fixer (`php-cs-fixer`, `csfix`, IDE "reformat file") on a file just because you edited a couple of lines in it — that rewrites unrelated pre-existing style (parameter alignment, missing `public`, trailing commas, blank lines) and turns a 3-line diff into a 40-line one, which makes the actual change harder to review and is exactly the kind of unrequested cleanup this project doesn't want. If phpinsights flags pre-existing style issues in a file you touched, leave them **unless** they cause the file to fail the actual configured thresholds (`shared/coding-standards.md`) — a few flagged lines with the aggregate score still comfortably above threshold is not a reason to reformat the file.

**Forbidden functions, lint gotchas, phpinsights thresholds.** All in `shared/coding-standards.md` — read it before writing PHP, don't re-derive it from memory (it's the single source; don't duplicate it here either). It also has a **"Lessons from review"** section — mistakes a human or Copilot caught before on a Celesta PR. Check it, and after any review round that catches something new, add a bullet there so it doesn't repeat.

**Shared-library composer dependency.** If this ticket depends on a changed shared lib (`celesta-job-library`, `celesta-constants`, etc.), verify the microservice's `composer.json` already points to `"dev-<TICKET>"` (e.g. `"dev-CEL-7972"`) before writing code against it — never a stable version during development. Composer only gets bumped to a stable tag after QA/PO sign-off. If it's not pointing to the dev branch yet, flag it and fix that first.

**New migration filename.** Never hand-write the `Version<timestamp>.php` filename/class name — generate it with `docker exec <service>.php php bin/console doctrine:migrations:generate`, then fill in the generated stub's `up()`/`down()`. A hand-picked timestamp (especially one with lots of trailing zeros) is easy to collide with a real one and looks fabricated in review.

**Migration fixes mid-ticket.** If a bug in a migration surfaces during testing (e.g. a missing column) and **nothing from this branch has been deployed to a real/shared environment yet**, edit the existing migration file in place — roll back locally, edit, re-apply — rather than stacking a new migration. Only create a new migration once something from a prior one is already deployed somewhere real; that's the only thing that makes a migration "immutable history."

## Constants and jobs — never define locally
Never create constants inside a service (put them in `celesta-constants`) or Messenger job classes inside a service (put them in `celesta-job-library`). If the ticket needs either, stop and tell the user it has to be added to the shared library first, in its own dev branch.

**Adding a constant breaks a test in celesta-backoffice — every time.** `ConstantManager::getConstants()` reflects over *every* class under `vendor/lancasters/constants/src` and publishes all of them, so any new constant instantly appears in the `/constants` response. `tests/GatewayBundle/Controller/ConstantControllerTest.php` asserts that whole payload against a hand-maintained expected array, so it fails until the new key is added there — even when the ticket has nothing to do with backoffice, and even when CI is the first place you notice. After adding anything to `celesta-constants`, update that test's expectation in the same ticket.

**The backlog is structural, and paying it is NOT out of scope.** Constants get added for whichever service needs them — usually not backoffice — but backoffice is where every one of them surfaces. Nobody updates that test until a ticket forces them to, so the gap between the constants library and backoffice's expectation grows quietly, and the next ticket that touches constants in backoffice inherits the whole balance. Expect the failure to include other people's constants alongside yours.

This is the one place where "don't change what the ticket doesn't need" does **not** apply: the test asserts the entire payload, so it cannot pass with only your keys added. Reconcile the whole thing. Tell the user when the inherited part is large — a two-constant ticket with a sixty-line test diff needs that explanation, and the size is a fact about the backlog, not about your change.

Two practical notes:
- Use `git diff origin/master...HEAD` inside the constants library to separate your constants from the ones that merely came along with master. Add both, but know which is which — you own yours, you're only settling the rest.
- The assertion is `assertEquals`, so key order doesn't matter. Derive expected values from the constant class itself, never from the CI diff text — a `null` constant used as an array key becomes `''`, and copying the CI output hides that.

## Next
Hand off to `ticket-review`.

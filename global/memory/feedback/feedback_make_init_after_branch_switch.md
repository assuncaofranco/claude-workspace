---
name: feedback-make-init-after-branch-switch
description: "Run `make init` after any big code change (branch switch, large merge/rebase, big drift from master) before trusting test results in a Celesta service; also, `make test` only migrates the test DB, not dev — migrate dev explicitly before live/manual verification"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 99bb98c2-81ae-4619-8f28-d661fa872735
  modified: 2026-08-31T14:36:37.007Z
---

After switching branches (especially onto/from a branch with significant drift from master) or any other large code change, run `make init` in the affected service before trusting `bin/phpunit`/`make test` results.

**Why:** Docker containers bind-mount the working directory, so PHP source changes are picked up live — but Doctrine's metadata/proxy cache and the dev/test databases are NOT automatically kept in sync with the checked-out code. Concretely hit this on [[project_cls1843_cls1912_currency_nullable]]: after checking out a fresh branch 111 commits ahead of an old one, `bin/phpunit` produced 19 spurious errors (`ReflectionException: Property ...::$updatedAt does not exist`) that had nothing to do with the actual code — the entity genuinely didn't have that property; it was stale Doctrine cache/test-DB schema left over from before the branch switch. `make init` (`docker compose up -d --force-recreate` + `install.sh --yes`: composer install, cache clear, DB drop/recreate, migrations, fixture reload) fully resolved it — 1522/1522 PHPUnit, 944/944 Behat scenarios passed clean afterward.

**How to apply:** Before reporting a test failure as a real regression right after a branch switch/merge/rebase, first rule out stale cache/DB by running `make init` (check the service's own Makefile for the exact target — celesta-promotion has both `init` and a `test` target that drops+recreates+migrates the test DB, which also helps but is narrower than full `init`). Don't silently work around it yourself otherwise — this is still a stack/cache problem, so if `make init` isn't available or doesn't resolve it, escalate per [[feedback_ask_before_workaround_on_stack_problems]] rather than improvising a fix.

**Related gotcha, same ticket:** `make test` only migrates the *test* database, never the dev one — writing a new migration and running `make test` leaves the dev DB's schema stale. On CLS-1843-CLS-1912 this produced a live end-to-end repro that silently failed post-fix (queue message consumed, no error logged, no row created) because the dev `player` table still had `currency NOT NULL` — a `NotNullConstraintViolationException` was thrown inside the message handler with no visible log line, easy to mistake for the fix not working. Fix: after adding/editing a migration, explicitly run `docker compose -f docker-compose.dev.yml exec php bin/console doctrine:migrations:migrate --no-interaction` (no `--env=test`) against the service's dev DB before trusting any live/manual verification through it.

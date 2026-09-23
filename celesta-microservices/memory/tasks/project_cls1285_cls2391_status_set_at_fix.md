---
name: project_cls1285_cls2391_status_set_at_fix
description: "CLS-1285-CLS-2391 (status_set_at fix) — implicit Doctrine listener-ordering bug pattern found in review, and the correct composer pattern for an unreleased shared job-library change across services"
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-21T06:13:00.431Z
  originSessionId: 2d5abbaf-0b46-4e8e-a40c-ff5fac3b4a24
---

Ticket CLS-1285-CLS-2391 (wallet→promotion `status_set_at` not propagating on bonus PLAYED/rollback/restored transitions) surfaced two reusable findings, beyond the ticket itself. See [[project_bonus_model_field_removal_risk]] for the broader bonus wallet↔promotion migration this belongs to.

## Finding 1 — implicit Doctrine listener ordering is a real, findable bug class in celesta-wallet

`BonusPlayedListener` (`BonusBundle`) sets `BonusSubBalance.status = PLAYED` and does its own `$em->flush()` — that flush is what fires the entity's own `#[ORM\PreUpdate]` callback populating `statusSetAt`. `RewardAssetPlayedListener` (`SubBalanceBundle`) reads that same `statusSetAt` and dispatches it to Promotion. Both are tagged on the same Doctrine event (`postFlush`) with no `priority` — so which one runs first was decided only by bundle import order in `config/services.yaml` (`@BonusBundle` before `@SubBalanceBundle`). It worked, but by accident: reordering those two import lines, or adding any new `postFlush` listener without a priority, would make the dispatched job silently carry `null` instead of the real timestamp — no error, no test failure (the unit tests mock the getter, so they don't exercise real listener ordering).

Fixed by adding explicit `priority: 10` to the tag on the "sets status, triggers persistence" listener (`BonusPlayedListener`, and its free-rounds twin `BonusPlayedFreeRoundsListener`), leaving the "reads it and dispatches" listener (`RewardAssetPlayedListener`/`RewardAssetPlayedFreeRoundsListener`) at the default priority 0.

**How to apply:** any time two Doctrine ORM listeners on the same entity/event have a "one must run before the other" dependency, check whether that's enforced by an explicit `priority` tag or only by accident of service registration order. This pattern is worth grepping for elsewhere in celesta-wallet/celesta-promotion (any `doctrine.event_listener` pair on `onFlush`/`postFlush` where one listener's output depends on another's side effect) — it's exactly the kind of bug that survives unit tests because mocks bypass the real ordering, and only shows up in an end-to-end run.

## Finding 2 — correct composer pattern for an in-development shared library, before its release tag exists

celesta-wallet and celesta-promotion both depend on `lancasters/job-library` (normally pinned to a released tag, e.g. `^3.121`). This ticket needed a job-library change (new field on 3 job classes) landed and testable in both consuming services *before* that change is tagged/released.

**Wrong approach (tried and reverted):** adding a local `path`-type repository to `composer.json` (`{"type": "path", "url": "./.job-library-local"}`) pointing at a manually-placed copy of the job-library repo, with the constraint set to `"@dev"`. This leaves an entire copy of another repo sitting inside wallet/promotion, untracked and *not* covered by `.gitignore` by default — a stray `git add .` would commit it whole. It also isn't reproducible by anyone else or by CI.

**Correct approach (what the fix actually shipped with):** push the job-library change to its own named branch (here, the same ticket branch, `CLS-1285-CLS-2391`), then set the constraint in the consuming service's `composer.json` to `"lancasters/job-library": "dev-CLS-1285-CLS-2391"` and run `composer update lancasters/job-library`. Composer resolves `dev-{branch}` against the already-configured private Packagist mirror (`repo.packagist.com/lancastersolutions`) via the branch pushed to GitHub — no local path, no untracked directory, and it's usable by CI/anyone with the branch pushed.

**How to apply:** this is the standard pattern for any coordinated change to `celesta-job-library` or `celesta-constants` (or any other shared library governed by the "must be created in the library, not the service" rule in the global CLAUDE.md) that needs to be tested end-to-end across services before a release tag exists. Once the library PR merges and a real tag is cut, swap `dev-{branch}` back to the normal `^X.Y` constraint and re-run `composer update` — existing version constraints in the consuming services usually already cover the next tag, no further `composer.json` edit needed.

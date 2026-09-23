---
name: project-cel7576-review-cleanup
description: "CEL-7576-2 review cleanup — getByBonusId removed (dead code), Flipper FR8/FR9 never implemented (deferred), RefundHandler 404 is intended because Promotion moved from master into CEL-7576"
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

CEL-7576-2 (`celesta-wallet`) review cleanup, decided 2026-06-17:

- **`getByBonusId()` removed** from `BonusSubBalanceRepository` — dead code, zero prod callers.
  Its only test file (`tests/SubBalanceBundle/Repository/BonusSubBalanceRepositoryTest.php`,
  4 tests, all `getByBonusId`) was deleted entirely. `RefundHandler` uses
  `getActiveByBonusIdAndWallet()` (walletId + non-terminal statuses), NOT `getByBonusId`.

- **FR8/FR9 (Flipper flag gate) were NEVER implemented** despite the plan marking them `[x]`.
  `FlipperClient`/`FeatureFlagService` do not exist in `src/Library/`; no Flipper refs in
  `config/` or `.env.test`; migration `Version20260427103138.php` does not exist on the branch.
  Plan/spec corrected to mark them `[ ]` / `_(Deferred)_`.

- **RefundHandler 404 contract change is intended, no external coordination needed.** Refund of a
  terminal bonus now returns 404 instead of a workflow error. The Promotion bonus path **was in
  master and is now owned/redefined inside CEL-7576**, so there is no frozen master-era external
  consumer to break — the 404 is defined by this ticket. Do NOT re-raise "confirm with promotion
  team" or propose reverting to `getByBonusId`.

**Why:** keeps the branch aligned with the standing rule — change only what the
sub_balance→BonusSubBalance migration strictly requires; everything else stays identical to master.

Validated: 58 tests / 270 assertions green (SubBalanceBundle/Repository + RefundHandlerTest +
BonusControllerTest). See [[project-cel7576-union-getfilteredbonuses]] and [[project_cel7576_cls848_status]].

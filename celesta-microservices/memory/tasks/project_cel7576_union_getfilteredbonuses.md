---
name: project-cel7576-union-getfilteredbonuses
description: "CEL-7576-2 getFilteredBonuses must match master (NO unionBonuses); archive test counts at 1/3 are correct, not a masked regression"
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

## getFilteredBonuses union — RESOLVED, matches master (2026-06-17)

In `celesta-wallet` CEL-7576-2, `getFilteredBonuses` in
`src/SubBalanceBundle/Repository/BonusSubBalanceRepository.php` must end with
`return $this->getBonuses($filter);` — **NO conditional `unionBonuses`**. Verified against
master (merge-base `0c2efb1d6`): master's `getFilteredBonuses` and the `getAllBonuses` hotfix
branch both use `getBonuses` (no union) since CEL-8396 `b185bcbe3`.

`unionBonuses` does `UNION ALL` of `sub_balance` + `archive_sub_balance`. The `sub-balance:archive`
command MOVES a row to `archive_sub_balance`. Without union, `getFilteredBonuses` reads only
`sub_balance`, so an archived row disappears and the count drops by 1.

**The test count reductions were CORRECT, not a masked regression:**
- `BonusControllerTest::testBonusListAfterMovingToArchive` — this test does NOT exist in master
  (new on the branch). Line ~212 (ownerIds + archived statuses → getFilteredBonuses) = **1**.
  Line ~223 (bonusModelIds only, no ownerIds → getAllBonuses hotfix) = **1** (CEL-8396).
- `SubBalanceRepositoryTest::testGetFilteredSubBalances` line ~85 = **3** — same as master.

A colleague flagged the conditional union as a leftover ("get rid of that, bonus is not archived
anymore, see b185bcb"). User's standing rule: **change only what the sub_balance→BonusSubBalance
migration strictly requires; everything else stays identical to master.** Restoring the union
diverges from master → wrong. The legitimate branch diffs in these methods are migration-only
(null-safe `bonusModel`, new `getActiveByBonusIdAndWallet` etc.).

Validated: 43 tests / 232 assertions green (BonusControllerTest + SubBalanceRepositoryTest).

See [[project_cel7576_test_failures]] and [[project_cel7576_cls848_status]].

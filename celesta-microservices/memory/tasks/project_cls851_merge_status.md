---
name: project-cls851-merge-status
description: "CLS-392-CLS-851 merged with master (committed 37d8f3148, pushed); 3 fixes verified; PENDING full suite on final tree"
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

`celesta-wallet` branch **CLS-392-CLS-851**: master (`c4f99e4d8`, PR #1628 = CEL-7576-2 with
migration) was merged in. Merge **committed as `37d8f3148 "CLS-851"` and pushed** to
origin/CLS-392-CLS-851. Working tree clean.

**Only conflict was `BonusListener.php`** — resolved by KEEPING master's guard
`getBonusModel() !== null` (NOT the old `getBonusId() === null`, which was a pre-fix regression
on the branch) AND keeping CLS-851's additive `updatedPlayedEntities` feature. Verified intact in
the commit: guard appears as `getBonusModel() !== null` (no getBonusId), `updatedPlayedEntities`
present.

**The 3 fixes the PO asked about — all verified green** via
`tests/Bonus/PromotionBonusFlowTest.php` (5/5, 22 assertions):
- **wagering** (no premature BONUS_WITHDRAW on partial bet) — fix from **master** (CEL-7576):
  `TransactionBetWagerListener:103` `getWagerWinAmount() === null` guard.
- **cancel** (BONUS_REFUND on cancel) — fix from **master** (CEL-7576): ClaimHandler does NOT set
  total_balance; it comes from BONUS_DEPOSIT, so the cancel guard passes → REFUND in the
  `updatedCanceledEntities` block.
- **played** (mark played zeros bonusBalance via BONUS_WITHDRAW) — **this is the CLS-851 fix**
  (`updatedPlayedEntities` block). Spec: `sdd/_specs/CLS-851.md` (promotion bonus consumed on
  promotion side must decrement wallet bonusBalance).

**PENDING for next session (2026-06-19):** full PHPUnit suite was NOT yet confirmed green on the
final merged tree (the merge pulled in lots of master evolution — ResponsibleGamingLimit,
BetManager, CLS-1291/CLS-439, new migration Version20260618120000). The targeted test passed but
run `docker compose -f docker-compose.dev.yml exec php php bin/phpunit` (full) to validate the
rest before considering the merge fully done. lancasters/constants is at `^1.316` (installed).

See [[project_cel7576_test_failures]] (the guard rule) and [[project_cel7576_cls848_status]].

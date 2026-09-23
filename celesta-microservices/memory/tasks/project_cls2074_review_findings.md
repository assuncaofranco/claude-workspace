---
name: project_cls2074_review_findings
description: CLS-2074 backfill script (bonus_id/reward_type in sub_balance) review findings — blockers before it can run against prod
metadata: 
  node_type: memory
  type: project
  originSessionId: 0cbf10c0-0cf5-486a-baf3-b7b58b7083f0
  modified: 2026-08-05T12:04:54.651Z
---

CLS-2074 (celesta-scripts, branch `CLS-2074`, script/CLS-2074/BackfillSubBalanceBonusData.php)
reviewed 2026-08-05 — report-only, no code changes made (user explicitly chose report-only scope).

**Why this matters**: it's a prod-data backfill over ~30M rows in `sub_balance`/`archive_sub_balance`,
write mistakes are effectively irreversible at that scale.

**Blockers found** (verified against actual code in celesta-wallet/celesta-promotion, not just the
branch's own spec/plan docs):
1. celesta-wallet PRs 1812/1819 (adds+populates `reward_type`) are NOT on `master` yet — only on
   unmerged branches `CLS-1285-CLS-1925` / `CLS-1285-CLS-2064`. `TransferSubBalanceToArchiveCommand`
   on master doesn't copy `reward_type` when archiving.
2. The spec/plan's core justification for dropping the Promotion DB connection + player_id check
   (that the ticket originally required) is factually wrong: CEL-6848 permanently skips migrating
   rows in 4 categories (`null_bonus_model_id`, `bonus_model_not_migrated`, `player_unresolved`,
   `orphan_wallet`), and `promotion.bonus`'s id-space isn't exclusive to CEL-6848 (a native claim path
   via `RewardOfferService`/`new Bonus()` isn't flag-gated). So `bonus_id = id` can silently point at
   a nonexistent bonus, or at a different player's bonus, and the script has no way to detect either
   since it never connects to Promotion.
3. Real implementation bug (not just design): in `sweepTable()`, the local `$lastId` cursor advances
   before the batch's commit succeeds/fails. A failed batch's row range gets silently, permanently
   skipped once a later batch in the same run succeeds and persists a cursor past it — only
   `--reset-cursor` (full resweep) would catch it. Violates the resumability acceptance criterion.
4. The required test file (`tests/CLS2074/BackfillSubBalanceBonusDataTest.php`) was committed then
   deliberately untracked from git twice (commits "Remove test class from version control", "Untrack
   test class again", same author). No test coverage currently exists on the branch. Recoverable via
   `git show 743e158^:tests/CLS2074/BackfillSubBalanceBonusDataTest.php`.

**How to apply**: don't approve this script for a prod run until the team decides how to close finding
2 (reintroduce Promotion connection + player_id check / filter out CEL-6848-skipped rows / accept
documented residual risk), finding 3 is fixed, and the test suite is restored and passing. Full
findings with file:line citations are in the plan file
`/home/lucas/.claude/plans/cls-2074-review-e-teste-sharded-nest.md`.

Related: [[project_cel7576_cls848_status]], [[project_cls850_scope]] (same sub_balance/bonus domain).

---
name: project_cls2064_review_and_cls1925_handoff
description: "CLS-2064 owns the reward_type/resolveRewardType mechanism; what CLS-1925 must drop, keep, and how they collide (migration + deploy order)"
metadata: 
  node_type: memory
  type: project
  originSessionId: f81a1a59-516c-4616-9182-75e10a63c4e4
  modified: 2026-08-04T12:19:57.029Z
---

CLS-1285-CLS-2064 (colleague's ticket) generalizes the "bonus type without BonusModel" fix that
CLS-1285-CLS-2064 took over from our CLS-1925. Reviewed 2026-07-31; branches `CLS-1285-CLS-2064`
exist in wallet + promotion, 58 affected tests green.

**What CLS-2064 now OWNS (CLS-1925 must DROP its duplicates of these and rebase on CLS-2064):**
- `sub_balance.reward_type` + `archive_sub_balance.reward_type` columns (migration).
- Type resolution: `RewardTypeResolver` SERVICE (`src/SubBalanceBundle/Service/RewardTypeResolver.php`,
  `resolve(BonusSubBalance): ?string`, flag-aware `shouldRouteBonusToPromotion()`) — 2064 EVOLVED from an
  entity `resolveRewardType()` method to this injected service. Plus `reward_type` field on both entities
  and BonusModelManager setting it for legacy.
- Claim flow: `Claim.rewardType` (+Assert\Choice), `ClaimType` field, `ClaimHandler::setRewardType`.
- Promotion `BonusListener` sends `'rewardType' => $rewardConfiguration->getType()` in claim payload.
- The played/grant listeners call `$rewardTypeResolver->resolve($entity)`. 2064 also added
  `TransferSubBalanceToArchiveCommandTest` (my review finding #2 addressed).

**What CLS-1925 KEEPS (its ONLY unique parts — NO schema/migration/entity change):**
- `GameTransactionController` bonus_id resolution + `BonusSubBalanceRepository::getByBonusIdAndWallet`
  (the win-credit-by-bonus_id fix — defect #1).
- `splitFreeRounds` `validityPeriodTo !== null` guard (defect #3).
- Win-credit + terminal-status + credit→played e2e tests in PromotionBonusFlowTest.

**bonus_id index → DROPPED (user decided):** the existing `wallet_id` index already bounds
`getByBonusIdAndWallet` to one wallet's few rows, so no dedicated bonus_id index. CLS-1925 therefore has
NO migration and NO schema change.

**EXECUTED 2026-08-03 (2064 not yet in master):** on branch CLS-1285-CLS-1925 — Phase 1 reset the
reward_type overlap files to master + `git rm` our migration & our BonusPlayedFreeRoundsListenerTest
(commit `b4f7cef22`); Phase 2 `git merge CLS-1285-CLS-2064` (NO conflicts). Result = 2064 base + only
the defect files above. 69 affected tests green (PromotionBonusFlowTest 10/10 incl. the e2e). Decided
NOT to re-add the listener unit test (e2e covers it; listener/service is 2064's). When 2064 lands in
master, merging master collapses the 2064 part of this branch's diff.

**CLS-1285-CLS-1925-2 (old migration-only ticket) is OBSOLETE — close its PR.** Its only real content
is the reward_type migration, functionally identical to CLS-2064's (same SQL; only getDescription differs).
CLS-2064 now delivers that migration via its own branch `origin/CLS-1285-CLS-2064-migration`. CLS-1925
carries no migration. So the "migration deploys first" artifact is now `CLS-1285-CLS-2064-migration`, not `-2`.

**Deploy/merge order:** CLS-2064 (migration PR `CLS-1285-CLS-2064-migration` → wallet code → promotion)
FIRST, then CLS-1925 (depends on reward_type/resolveRewardType existing). See [[project_cls850_scope]] for the sync-loop
guard context and [[reference_db_query_from_containers]] for verifying rows.

**CLS-2064 review — the ONE real defect (user agreed):** `TransferSubBalanceToArchiveCommand` was not
updated → archival/restore drops `reward_type`. FIX IS ONE PLACE: add `reward_type` to the `$baseQuery`
SELECT column list (~line 313-317); the INSERT auto-includes it because `insertSubBalances()` derives
its columns from `array_keys()` of the selected rows (SELECT and INSERT column sets are identical by
construction, and both archive+restore share `$baseQuery`). Non-defects: migration overlap intentional
(above); `required=>false` on ClaimType is form-view only, not a real constraint (validation is
`Assert\Choice` on the model) — ignorable; BonusPlayedFreeRoundsListener has no unit test (optional
nice-to-have, not a blocker). Logger/guard removal is deliberate (documented in the plan).

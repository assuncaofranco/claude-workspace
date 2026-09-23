---
name: project-cel7576-test-failures
description: "RESOLVED — BonusListener OFFERED→CLAIMED guard in CEL-7576-2: correct discriminator is getBonusModel()!==null, not getBonusId()"
metadata:
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

## BonusListener OFFERED→CLAIMED guard — RESOLVED (2026-06-17)

In `src/BonusBundle/EventListener/ORM/BonusListener.php`, the OFFERED→CLAIMED block (`onFlush`,
the `getScheduledEntityUpdates` loop) runs `setClaimedAt` + `setValidityPeriodTo` + `grantFreeRound`.
In master this block had **no guard** — it ran unconditionally for every OFFERED→CLAIMED transition.

CEL-7576-2 added a guard. Three candidate forms, only one is correct:

| Guard | Effect | Verdict |
|-------|--------|---------|
| `! $entity->getBonusId() === null` | always false (`!` binds tighter than `===` → `bool === null`) → block dead | original BUG |
| `$entity->getBonusId() !== null` | bonusId is null for BOTH traditional AND RewardManager bonuses → block still dead → claimedAt/validity/freeRounds silently dropped for traditional bonuses on offer→claim (PATCH) and manual+auto-claim flows | REGRESSION vs master |
| `$entity->getBonusId() === null` | runs for traditional AND RewardManager promotion bonuses → wrongly sets claimedAt=now on promotion bonuses | broke ~35 tests |
| **`$entity->getBonusModel() !== null`** | runs ONLY for traditional bonuses; excludes all promotion bonuses | **CORRECT** |

**Why `getBonusModel() !== null` is right:** the real traditional-vs-promotion discriminator is the
bonusModel, not bonusId. It matches the insert-path guard at line ~53 of the same method. Validated:
256 bonus tests green (tests/Bonus, BonusModelController, BetAndWin, GameTransactionController,
BonusControllerTest, BonusBundle, SubBalanceBundle).

**Why the regression was invisible:** `mockFreeRoundsGrant()` (tests/Traits/MockCurlClientRequestsTrait.php)
is a LOOSE stub — it registers an HTTP response but does not assert the call happened. No test asserts
claimedAt/validityPeriodTo on the offer→claim path. So the dead block passed CI silently.

See [[project_cel7576_status]] family.

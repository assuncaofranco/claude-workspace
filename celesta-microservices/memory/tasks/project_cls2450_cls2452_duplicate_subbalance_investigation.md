---
name: project_cls2450_cls2452_duplicate_subbalance_investigation
description: "CLS-2450-CLS-2452 — root-cause findings for duplicate sub_balance (free_round) rows created by an instant_reward/manual promotion_configuration; two distinct bugs confirmed, reproduction test plan still pending"
metadata: 
  node_type: memory
  type: project
  originSessionId: eb7840a9-5341-4136-b2e0-5c9f00fdd8be
  modified: 2026-08-25T09:11:00.177Z
---

Ticket **CLS-2450-CLS-2452**: a `promotion_configuration` (id 312, domain 53, `type=instant_reward`, `engagement_model=manual`, name "[PROMO CODE] CHURN - D15 | 5 FS R$0.20 | FS ON LOGIN", schedule 2026-08-24→2026-09-06, segment 75512, `player_promotion_limit=1`) with a single `reward` (id 732, `type=free_round`, `bonus_model_id`/`reward_configuration_id=121340`, quantity 5) produced **two `sub_balance` rows in celesta-wallet for the same player** instead of one. User's initial hunch: "pode ser concorrência (falta de locks)" — confirmed correct, but it's actually **two separate concurrency bugs**, not one.

**Why this matters:** both bugs are real and currently unmitigated in prod for this campaign; any fix needs to address both, or at minimum the wallet-side idempotency gap that lets either one produce a real duplicate.

## Bug A — dispatch-level duplicate (same Promotion rewarded twice) — ROOT CAUSE CONFIRMED

Code: `celesta-promotion/src/AppBundle/PromotionConfiguration/Standard/Handler/RewardHandler.php`, method `acquireConfigLock()`. It acquires a Redis lock keyed `promotion_config_%d` (per **config**, not per player/promotion), then calls `$this->entityManager->refresh($promotion)` with **no lock mode** (no `FOR UPDATE`). The only other explicit `beginTransaction()` in the whole promotion codebase is `celesta-promotion/src/AppBundle/Command/ManagePromotionSchedulesCommand.php` (the `promotion:manage-schedule` cron), which under MySQL's default `REPEATABLE READ` can hold a snapshot fixed *before* a concurrent commit, so the post-lock `refresh()` can still show `ENGAGED` even though the promotion was already rewarded by another flow. `isPromotionEligible()` (checks only `status !== REWARDED/EXPIRED`) then wrongly passes, and the reward fires a second time against celesta-wallet.

**Confirmed via real prod data** (not just code reading) — player promotion id `143171` (wallet_id `2315198`, player_id `2319757`):
- `promotion.engaged_at = 2026-08-24 21:02:30` == `sub_balance` #1 (`id 35478056`) `created_at` — the login-triggered opt-in's synchronous reward (`InstantRewardService::rewardIfEligibleOnEngagement` → `rewardNow`, fired in the same request as the opt-in, since the promo is literally "FS ON LOGIN").
- `promotion.updated_at = 2026-08-24 21:02:31` == `sub_balance` #2 (`id 35478057`) `created_at` — a **second** call to `RewardHandler::handle()` for the *same* `promotion_id`, exactly 1 second later.
- The ~1s gap rules out "two cron passes minutes apart"; it fits the cron's `processInstantRewardRewardsForCurrentOccurrence()` (in `celesta-promotion/src/AppBundle/Service/ScheduleHandlingService.php`) querying `ENGAGED` promotions for config 312 in the narrow window between the opt-in's commit and the synchronous reward's commit — i.e. **schedule (cron) colliding with URL (manual opt-in endpoint) almost simultaneously**, confirming the user's instinct not to dismiss that combination.
- `amount` differs between the two sub_balance rows (1.00 vs 0.20) — this is **not** a second bug, just two independent free-round playthroughs with different win outcomes (status `played` vs `canceled`).

Found via safe indexed queries on `sub_balance` (`bonus_model_id` index — `promotion_id` has **no index**, added later via `Version20250820075443.php`, so never filter `sub_balance` by `promotion_id` alone on the raw table): grouping `WHERE bonus_model_id=121340 AND discr='bonus' GROUP BY wallet_id, promotion_id HAVING cnt>1` — only **5 of 36** duplicated wallets share the same `promotion_id` (this bug); the other 31 don't.

**Cron×cron ruled out**, not just untested: `celesta-argocd/microservices/promotion/kustomize/base/promotion-cronjobs.yaml:56` sets `concurrencyPolicy: Forbid` and `schedule: "* * * * *"` — k8s will never run two overlapping instances. Confirmed via real APM trace (id `6a8cb15000000000ce66b11fece2d450`), not just DB timestamp correlation: root span is the cron run (21:02:08→21:02:33, 25s of every 60s), and within that same trace the cron itself calls `GET /api/domain/53/wallet/2319757` (21:02:30.880) then `POST .../offer` (21:02:30.953→200) producing `sub_balance` 35478057 — i.e. the cron's own single sweep issued the duplicate offer, not a second cron instance. Because config 312's occurrence is continuously active for the full 14-day window and each sweep takes ~25s of every 60s, **~42% of the time there's a sweep in flight** — any opt-in landing in that window collides. This is structural, not a rare coincidence; explains why 36 players got hit.

**Two live candidates for *why* the cron's re-check saw the promotion as still-payable** (not closed from code alone; ruled out: Redis lock plumbing is sound — single shared Redis, `RetryTillSaveStore` blocks correctly — and no client-side curl retry exists):
- **(a)** stale `REPEATABLE READ` snapshot in the cron's transaction, held open across `EntityManager::refresh($promotion)` in `acquireConfigLock()` — original hypothesis, still viable.
- **(b)** NEW, distinct mechanism — `InstantRewardService::rewardNow()` swallows **every** `\Throwable`. If the opt-in path's wallet call succeeds (pays) but something *after* that throws before `markAsRewarded()` persists, the promotion stays `engaged` with the bonus already paid — no staleness/race needed, the cron then legitimately re-pays a genuinely-still-`engaged` row. Different fix than (a): stop swallowing the exception / reorder mark-then-pay, vs. locking read.
- Also worth checking: whether `celesta-promotion` reads through a DB **read replica** (`config/packages/doctrine.yaml`) — replica lag would be a third, unrelated mechanism for the same symptom. Not yet checked.
- Next cheap step to disambiguate: check celesta-promotion logs around 21:02:30-31 for promotion_id 143171/player 2319757 for a swallowed exception (confirms b); check doctrine.yaml for replica config (confirms/rules out c).

## Bug B — engagement-level duplicate (two different Promotion rows for the same player) — MECHANISM NOT YET CONFIRMED

31 of the 36 duplicated wallets have **two different `promotion_id` values** for the same `wallet_id`+`bonus_model_id`, each rewarded exactly once. This means the duplication started at **opt-in/engagement**, not at reward dispatch. Only plausible code-level cause found so far (not yet confirmed against timing/logs the way Bug A was): `PlayerPromotionLimitValidator::validate()` (`celesta-promotion/src/AppBundle/PromotionConfiguration/Standard/Validator/Engagement/PlayerPromotionLimitValidator.php`) only counts already-`REWARDED` promotions via a plain `SELECT COUNT`, with no lock and no DB unique constraint on `promotion(player_id, promotion_configuration_id)` — a classic TOCTOU: two concurrent opt-in calls for the same not-yet-engaged player could each pass the check and each insert their own `ENGAGED` row via `PromotionRepository::saveOptIn()`. Since the cron never creates engagements for `manual`-type configs (`getPromotionConfigurationsToEngage()` is hardcoded to `automatic` only), this bug's collision pair is almost certainly **URL × URL** (two near-simultaneous calls to the opt-in endpoint), not schedule-related — but this hasn't been verified the way Bug A was, so don't treat it as settled.

## Wallet-side gap (celesta-wallet) — applies regardless of which promotion-side bug fires

`BonusModelController::postOfferBonusModelAction()` (`celesta-wallet/src/ApiBundle/Controller/BonusModelController.php`) has **zero idempotency**: `OfferConditionChain::validate()` returns immediately for `OFFERING_METHOD_MANUAL` bonus models, skipping all duplicate-offer checks; no unique constraint on `sub_balance`; no lock/transaction around the `persist()+flush()`. A related bug (`sdd/_specs/CLS-1285-CLS-2048.md` in celesta-wallet) already documents this class of issue in the *claim* path and explicitly punted a real fix (unique key on `(wallet_id, bonus_id)`) as out of scope — that fix never touched this `/offer` endpoint.

## Safe query patterns used (sub_balance has millions of rows)

Never filter `sub_balance` by `promotion_id` (unindexed). Safe indexed filters: `bonus_model_id` (`IDX_9F987F7A775FA43D`), `wallet_id` (`idx_discr_wallet_id`/`idx_wallet_id_discr_status`), `discr`+`status`. Always `EXPLAIN` before running on prod; look for `type: const/ref` and a small `rows` estimate, not a full scan.

## Status / next step

Currently designing (in-chat, no doc per user's request — "não precisa criar o documento verboso de IA") a **local reproduction test plan** for both bugs before writing the fix, per user's explicit ask to test all plausible collision pairs (schedule×URL, cron×cron, URL×URL) rather than assume just one. See [[feedback_review_product_impact_not_just_current_code]] for the general review-lens habit that applies once a fix is proposed.

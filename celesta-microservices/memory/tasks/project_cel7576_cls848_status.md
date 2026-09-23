---
name: cel7576-cls848-status
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

# CEL-7576 / CLS-848 + CLS-851 — Implementation Status

Branch CEL-7576 (ticket renamed CLS-848) + CLS-851 are implemented and passing tests.

## Core Change

- `NewSubBalance` entity deleted; `BonusSubBalance` is the single entity.
- `ClaimHandler` creates promotion-system bonuses (`isFromPromotionSystem()` = `bonusModel === null`).
- CLS-851 bug (cancel not creating `BONUS_REFUND`) was fixed by removing erroneous `setTotalBalance()` in `ClaimHandler` — `TransactionListener::setSubBalanceBalance()` sets `total_balance` correctly via `BONUS_DEPOSIT` transaction.

## Why

Promotion system creates bonuses directly via `POST /bonus-transaction` (action=claimed) without a `BonusModel`, bypassing the old offered→claimed flow.

## How to Apply

When working on any `BonusSubBalance` listener, always check `isFromPromotionSystem()` guards.

## Known Bugs Found by Code Review (not yet fixed)

- **CONFIRMED**: `BonusSubBalanceRepository::compareBonusesBy()` lines 899-900 — null crash when sorting by `offerPeriodFrom` with promotion bonuses present (promotion bonuses have no BonusModel, so `getOfferPeriodFrom()` returns null).
- **CONFIRMED**: `GiveBonusOnDepositListener::checkBonusValid()` line 134 — `getBonusModel()` used without null guard for non-promotion legacy bonuses with null `bonusModel`.
- **PLAUSIBLE**: `BonusPlayedListener` line 41 — guard removed allows double-flush for promotion bonus played transitions.
- **PLAUSIBLE**: `TransactionWinWagerListener`, `TransactionBonusDepositDirectListener`, `TransactionWinUpperListener` — no `isFromPromotionSystem()` guard; promotion bonuses with matching model string may trigger TTR incorrectly.

## CLS-848 Flipper Bug Investigation — Preprod-1

**Datadog error link:**
https://app.datadoghq.eu/apm/traces?query=env%3Apreprod-1%20status%3Aerror%20service%3A%28celesta-promotion%20OR%20celesta-gateway%20OR%20celesta-wallet%29%20-resource_name%3A%22synchronize%3Atransaction-aggregation%22&agg_m=count&agg_m_source=base&agg_t=count&cols=service%2Cresource_name%2C%40duration%2C%40http.method%2C%40http.status_code%2C%40_span.count%2C%40_duration.by_service&fromUser=false&graphType=flamegraph&historicalData=true&messageDisplay=inline&query_translation_version=v0&shouldShowLegend=true&sort=desc&spanType=all&storage=hot&traceQuery=&view=spans&start=1780675200000&end=1780676400000&paused=true

**Root cause hypothesis:** `FLIPPER_DATABASE_URL` in preprod wallet resolves to db name `pp1_flipper_` (trailing underscore) — likely a hidden character in the env var. This causes:
1. `PDOException` on Flipper DB connection
2. `FlipperClient` returns `false`
3. `ClaimHandler` returns 400
4. `sub_balance` never created

**Evidence:** Env var displays as `pp1_flipper` but Datadog traces show `pp1_flipper_`.

**Next step:** Run `printenv FLIPPER_DATABASE_URL | cat -A` inside the preprod wallet container to confirm hidden/trailing character.

---

## CLS-850-1 — Sub-Balance Sync (in progress)

- `SubBalanceSyncJob` created in celesta-job-library: `src/JobLibrary/Job/Wallet/SubBalanceSyncJob.php`
- `SubBalanceSyncListener` created in celesta-wallet: `src/SubBalanceBundle/EventListener/ORM/Bonus/SubBalanceSyncListener.php` (registered in `SubBalanceBundle/Resources/config/services.yml`)
- 3 new `FreeRoundConfiguration` subclasses created in celesta-promotion: `AleaV2FreeRoundConfiguration`, `PragmaticFreeRoundConfiguration`, `WazdanFreeRoundConfiguration` — discriminator map updated in `FreeRoundConfiguration.php`
- `SubBalanceSyncJobHandler` in celesta-promotion: still TODO
- Spec/plan for CLS-850-1 needs update to cover: `BonusModel` → `RewardConfiguration` sync scope, the 3 new `FreeRoundConfiguration` classes, and the full entity mapping scope

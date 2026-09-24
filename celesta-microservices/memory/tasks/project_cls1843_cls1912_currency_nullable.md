---
name: project-cls1843-cls1912-currency-nullable
description: Status of CLS-1843-CLS-1912 (celesta-promotion) — support bonus flows for players who register without a currency
metadata: 
  node_type: memory
  type: project
  originSessionId: 99bb98c2-81ae-4619-8f28-d661fa872735
  modified: 2026-09-01T10:50:50.474Z
---

**Ticket**: CLS-1912, subtask of CLS-1843 (follow-up of CLS-1727). Repo: celesta-promotion, branch `CLS-1843-CLS-1912-support-bonus-without-currency` (started fresh off master; a colleague's earlier branch was 111 commits stale and was declined — master had since refactored bonus issuance via `RewardSourceResolver`).

**Also touched**: `lancasters/celesta-fixtures` branch `CLS-1843-CLS-1912-support-bonus-without-currency` (pushed), installed in promotion as `dev-<branch>` — must be tagged and the constraint bumped before merge.

## Architecture learned (worth keeping)

- **A wallet cannot exist without a currency.** `WalletManager::createWallet(..., string $currency, ...)` — currency is non-nullable and part of wallet identity (`findOneByOwnerAndApplication($ownerId, $appId, $currency)`), one wallet per owner+application+currency.
- **Wallets are created lazily**, never manually: `TransactionalKernelListener` (any wallet request carrying a currency), `PaymentTransactionJobHandler` (payment sale/initiated), `InitiateWalletJobHandler` (registration, only when currency present), plus `CreateMissedWalletCommand` as a repair tool. So a currencyless player gets a wallet at their first transaction.
- **Consequence**: a player can have a currency and still have no wallet. `BonusOfferAllowedValidator` reads the wallet, so engagement stays blocked until one exists — correct, not a bug.
- **`Bonus` has no currency column**; it inherits the `RewardConfiguration`'s. On claim, `BonusListener::postWalletBonusTransaction` posts to Wallet and only *logs* failure — so a bonus issued to a walletless player would end CLAIMED with nothing credited (silent divergence). This is why **both** issuance paths must be blocked, not just the wallet one.
- **`move_bonus_to_promotion` flipper flag** decides per reward between the legacy wallet path (flag off — production today) and the promotion-owned `RewardConfiguration` path (flag on — soon). Mockable everywhere: unit via `FeatureFlagService` mock, Behat via `InMemoryFlipperClient` + `Given the :flag feature flag is on/off`. Asymmetry: flags default **on** in the test env, **off** in dev (empty `flipper_features`).
- **Engagement only ever matches `engagementModel: automatic`**, and every pre-existing fixture was `manual` — so no login could engage anybody. Added an `automatic` fixture with **empty `segmentIds`** (a non-empty list makes `PlayerSegmentMatchValidator` reject a freshly registered player, silently, because `Standard::dispatchEngagement` swallows exceptions in an empty `catch`).

## Two design decisions revised mid-implementation (both were mine, both wrong first)

1. **Reward guard covers both issuance paths**, not wallet-only. Original plan said a currencyless player could still receive a `RewardConfiguration`-linked bonus; the claim path above disproves it. Guard now sits before the rewards loop (also one log per context instead of per reward).
2. **Currency refresh is centralised in `PlayerManager::getPlayerById()` and flushes.** First version put it at individual call sites with `persist()` only — verified live that the value is then **lost**, because a flow rejected by a validator never flushes, so Memberzone was re-queried forever. Now: `ensureCurrencyKnown()` mirrors the existing `ensureKycStatusKnown`, with try/catch degrading to the stale value (reading a player must not start depending on Memberzone), a flush (safe: both handlers validate before building anything), and per-request memoization (ReferAFriend resolves players in a loop).

## Status 2026-09-01 — implementation complete, not yet reviewed/committed

All 8 planned steps done. Suite: **1540/1540 PHPUnit, 944/944 Behat**. phpinsights above thresholds on every touched file. Newman collection: 7 requests / 9 assertions, 0 failures.

Live-verified end to end: control player registered with currency → engaged (1 promotion row); player registered without currency → created with `currency = null`, no engagement, nothing in `promotion-failed`; same player completes profile via `PATCH /player/information` → currency refreshed **and persisted**, engagement still pending a wallet (correct).

Reported but not fixed (other tickets): pre-existing `offering_status cannot be null` when creating a reward configuration with the flag off (`SetOfferingStatusListener` returns early — CLS-1285-CLS-2228); `RewardConfigurationController::offerReward` is shielded by the Backoffice's own currency pre-check but was hardened anyway since any service can call it directly.

Next: `ticket-review`, then commit/PR. See `global/rules/environment.md` for the dev-DB migration gotcha.

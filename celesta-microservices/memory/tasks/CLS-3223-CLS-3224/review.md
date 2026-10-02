---
name: cls3223-cls3224-review
description: "celesta-promotion PR #536 (Bohdan): validity expiry of claimed bonuses now waits for wallet confirmation; what the bug was and open review points"
metadata:
  node_type: memory
  type: project
  originSessionId: a8e5c18d-ceac-4588-89e8-7715a070c8c8
  modified: 2026-09-29T09:37:33.142Z
---

Review started 2026-09-29. PR celesta-promotion #536, branch `CLS-3223-CLS-3224`, author bogdanlinitskiy.

**Bug:** `BonusExpiryService::expireValidityBonuses` expired in promotion first, then called wallet
`POST /api/bonus-expiration`. Since CLS-1285-CLS-1898 the wallet takes the owner lock without waiting
and skips owners that are still locked after one retry (`BonusExpirationManager`), and the response was
ignored. Result: promotion `expired`, wallet sub_balance still `claimed`, so the player keeps usable bonus money.
The old code also expected `{expiredBonusIds: [...]}` in the mock, but the wallet returns a flat `array<int>`.

**Fix:** for the claimed path only, the wallet goes first and promotion expires only the ids that are
both in the chunk and in the wallet response (Copilot's intersect suggestion was applied). Ids the
wallet doesn't confirm are logged and stay claimed for the next run. Retrying is idempotent because
the wallet returns ids that are already expired. The offered path is unchanged.

**Open points (not posted yet):**
- A claimed bonus with no wallet sub_balance, or with one in played/canceled, is never confirmed.
  It stays claimed forever and logs an error every run. Before, it expired anyway.
  One way to get there: `BonusListener::postWalletBonusTransaction` swallows V2Exception.
- The same locked owner gets logged as an error twice, once by the wallet and once by promotion.
- The composer bump of constants from the dev-branch pin to ^1.337 is out of scope but harmless (v1.337 contains CLS-2594-CLS-3054).
- The wallet's OpenAPI annotation says the response is an array of BonusSubBalance. It's actually an int array (wallet-side, not this PR).

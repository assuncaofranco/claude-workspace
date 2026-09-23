---
name: project_cel6898_review_status
description: CEL-6898 (celesta-gateway) review in progress — move bonus-deposit validation Wallet→Promotion via Flipper flag; open concern about PaymentController diff to resolve 2026-06-19
metadata: 
  node_type: memory
  type: project
  originSessionId: 44a0d600-c08a-4d98-9219-e8acf2f8080d
---

CEL-6898 in **celesta-gateway** (branch `CEL-6898`). Reviewing a diff-vs-master. Goal: move
`ValidateDepositBonuses` from hardcoded Wallet to flag-routed Wallet/Promotion (`move_bonus_to_promotion`
Flipper flag). Incremental — **both paths must work** (flag OFF → Wallet, ON → Promotion). New infra:
`FlipperClient`, `FeatureFlagService`, `BonusFetcher`. Plan/spec in `.claude/_plans/CEL-6898.md` and `.claude/_specs/CEL-6898.md`.

**Review resolved 2026-06-19.** Did `git diff master`, trimmed to strictly-necessary, full suite green.

**RESOLVED — PaymentController diff is JUSTIFIED, keep it.** [PaymentController.php](celesta-gateway/src/Deposit/Controller/PaymentController.php)
~L194-206 + `validate(): ?string` + `ERROR_*` constants exist to **preserve master's exact error contract**
after the `BonusesDepositValidator` constraint was deleted. Master's OWN PaymentControllerTest already asserted
`{message:'Form validation error.', errors:['Invalid bonuses'|'Invalid bonuses claiming event'], code:VALIDATION_CONSTRAINT}`
(from the constraint) and `{message:'Deposit amount does not meet bonus deposit condition.', code:...}` (from the
handler). Reverting to the plan's "generic throw / accept the regression" would REGRESS behavior and break those
master-derived tests — opposite of minimal. So the plan's text was superseded by better backward-compat work.
`code` is injected globally by `ErrorCodeResponseSubscriber` (lancasters/symfony-components), not the controller.

**CHANGE APPLIED (only one):** reverted `config/packages/monolog.yaml` to master via
`git checkout master -- config/packages/monolog.yaml`. It was an out-of-scope test-logging change (3 CEL-6898
commits) that silenced test logs; nothing to do with bonus validation. Safe because the syslogudp handler services
it references still exist in `services_test.yaml`. NOT committed (user commits when ready). Diff is now 21 files.

**Tests GREEN after revert:** full `PaymentControllerTest` alone = OK 465 tests / 941 assertions; new unit/library
suites = OK 48 / 77.

**Left as-is (flagged, low priority, NOT changed — changing risks the suite):** `config/services_test.yaml`
hard-codes FeatureFlagService override=`false` + FlipperClient url=`''` → integration tests run the WALLET path;
`.env.test F_MOVE_BONUS_TO_PROMOTION=true` is therefore dead and the Promotion mocks added to PaymentControllerTest
are inert. Promotion path is covered only by unit tests. Honest but slightly misleading; reconcile only if desired.

**Other findings already established (don't re-derive):**
- Tests GREEN after user reinstalled: new unit suites pass (48 tests / 77 assert): ValidateDepositBonusesTest,
  BonusFetcherTest, FlipperClientTest, FeatureFlagServiceTest. Two controller fail-methods pass (148 assert).
  Earlier 148× HTTP 500 was a stale/uninitialized env; a later fixture `oauth2_client.PRIMARY` duplicate was MY
  concurrent-run collision on the shared test DB — neither is a code defect. Full PaymentControllerTest alone not
  yet confirmed (run was interrupted).
- Test-env wiring contradicts plan: `config/services_test.yaml` hard-codes FeatureFlagService override=`false` +
  FlipperClient url=`''` → integration tests run the **Wallet** path. `.env.test F_MOVE_BONUS_TO_PROMOTION=true`
  is overridden (dead). Promotion mocks added to PaymentControllerTest are **inert**. Plan step 12 ("test now
  queries Promotion") is false. Promotion path is only unit-tested, never integration-tested.
- `config/packages/monolog.yaml` (when@test) change is **out of scope** — sets main handler `type: 'null'`,
  silences app logs in test (hurts debugging). Verify it belongs to this ticket.
- Constants verified equal: Wallet `bonusModel` and Promotion `rewardConfiguration` share identical field strings
  (`claimingEvent`, `claimingEventCondition`, `depositAmountMin/Max`, value `'deposit'`), so `BonusFetcher`
  normalization works for both shapes. Nit: BonusFetcher uses Wallet constants for keys but ValidateDepositBonuses
  compares event to `PromoConstants::CLAIMING_EVENT_DEPOSIT` (works only because values match).
- Lint passes: FlipperClient style 97.6, BonusFetcher OK (min-style 85, min-complexity 0). Minor: lines exceed 120
  chars — FlipperClient:22,43,46 and BonusFetcher:59,60.
- Minor: `validate()` evaluates the flag twice (fetchBonuses + buildBonusMap); plan's dropped `$isPromotionPath`
  param to buildBonusMap would have avoided the double Flipper query.

Related: [[project_gateway_routing_pattern]].

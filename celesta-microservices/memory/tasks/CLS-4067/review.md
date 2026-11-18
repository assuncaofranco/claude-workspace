---
name: cls-4067-review
description: "Review of CLS-4067 (promotion #570) + CLS-3763 (wallet #1927), Rasoul's bonus currency guard under CLS-2962; 4 comments posted 2026-10-28"
metadata:
  node_type: memory
  type: project
  originSessionId: bfd9bf94-ec96-40c7-9cb1-3c128eb5aed7
  modified: 2026-10-28T13:17:46.921Z
---

Review as reviewer, author Rasoul. Merge order: promotion #570 before wallet #1927. Wallet #1927 had no findings.

Posted 2026-10-28 (all to Rasoul, product questions go through him to Pedro):
- PR #570 review 5681871057, RewardHandler.php:233: a wallet/CRM timeout in the guard is swallowed by the empty `catch (Exception) {}` in `Standard::dispatchReward` (and ReferAFriend); asked for a log with reward/promotion/player. **Blocking.**
- PR #570, RewardConfigurationController.php:417: BO offer uses `assertBrandEnables` (brand list only), so a player who already holds a wallet in a disabled currency gets 400. The parent's scope says "check only when a wallet would be created ... and bonus offer", so this is a defect; suggested `assertCanCredit`. **Blocking.**
- PR #570 global comment (first posted on Jira, Lucas deleted it there and wanted it on GitHub): plan says `offerForPromotionReward` is out of scope, PR covers it (4148b47), not blocking; and parent AC still refuses an offer "different from the player currency", CLS-3357 allows it, Rasoul to check with Pedro.

Round 2 (2026-10-28): Rasoul fixed the BO offer (`d56fc54`, `assertCanCredit`) and the log (`8394aeb`, logs then rethrows), and updated the plan (the AC question is now "Open questions", Pedro hasn't answered). New finding from the rethrow: in Multiplus, `processReward` catches the exception and the base `handle()` still flushes, so rewards persisted earlier in the loop are saved and credited while the promotion stays engaged, and the next qualifying bet issues them again. Standard has the same issue if another promotion flushes in the same event. The test only covers a failure on the first reward. Lucas sent it to Rasoul on Slack, not on the PR; waiting for his answer. **Not approved yet.**

Not commented: HTTP calls inside the cluster-wide campaign config lock (see [[locks]]), no Datadog numbers. Follow-up ticket for retry or operator visibility of a skipped reward was not raised.

**Why:** two wrong calls of mine on finding 2. First I called it ambiguity, then I withdrew it after reading only the AC and the "existing wallets keep working" line. The scope sentence that names bonus offer settles it.
**How to apply:** before classifying a finding as doc divergence or as not a defect, read the parent's Goal, Scope and AC together, not just the AC.

Master merge (2026-11-06, Rasoul out sick, Lucas asked): pushed `160a9176c` (merge) + `873ef5613`. Master had rewritten `DepositRewardClaimService` around a `Deposit` model and now refuses a deposit in a currency other than the reward's (CLS-3701-CLS-4196) *before* the guard. Kept master's version plus the guard. Silent conflicts git didn't flag: the guard test used the old `claimOnDeposit` signature, the new Standard `RewardHandlerTest` built `RewardOfferService` without the guard, and a new behat scenario (GBP deposit) didn't declare the brand's currencies. Stale `var/cache/test` gave 13 false 500s in the controller tests.

CI after the merge (2026-11-06), green on `d14a129`: (1) unit coverage gate at 100% (came with CLS-3544) needed a test for `BonusCurrencyNotEnabledException`; (2) Proteus PCPR-34 (reasons, ours, CLS-4163) failed the OpenAPI check on 404s, not Rasoul's fault: the suite was only enabled by QA on 2026-11-05 (QAA-1138), and 404 bodies come out as `{title, code}` (vendor `KernelExceptionSubscriber`) while `NotFoundSchema` required `message`. Changed the schema to `title` inside #570, Lucas's call. Still wrong: the hand-built 404s in `RewardLoader`/`RewardAggregatorLoader`/`PromotionConfigurationLoader` return `message` under the same schema; no Proteus test validates them today.

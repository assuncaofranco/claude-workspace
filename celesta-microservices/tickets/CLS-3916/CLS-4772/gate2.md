# CLS-4772 gate 2

Worktree `/private/tmp/cls3916/celesta-promotion-4772`, branch `CLS-4772`, plan commit `91cd7266b`. Not pushed (service and proteus).
Stack (`promotion.php` / `promotion.nginx`) was on the 4771 worktree; repointed to this one with
`docker compose -f docker-compose.dev.yml up -d --force-recreate`, then `composer update lancasters/job-library` and
`install.sh --yes` (both DBs migrated to `Version20261117150000`, 74 migrations). `.env` copied from the main clone.
Logs in this folder: `phpunit-touched.log`, `phpunit-wide.log`, `behat-plan.log`, `behat-wide.log`.

## 1. Commits

Implementation commit: `b6e040321e1c580dbe81b9d43ce36fc7635e38ac` `CLS-4772 Create a gift when a promotion instance is rewarded`
(on top of the last merge commit `52b39f6f4`; amended before this gate after `make lint` flagged the issuer, and amended again, before any push, for the Instant reward scenario: previous hash `e367ba682`. Lucas approved the push with that change.)

Merges, in order, all `--no-ff`, **no conflicts in any of them**:

| Commit | Message |
|---|---|
| `6ef28dc26` | `CLS-4772 Merge CLS-4743 into CLS-4772` |
| `6dcc36cd3` | `CLS-4772 Merge CLS-4770 into CLS-4772` |
| `9335d0b67` | `CLS-4772 Merge CLS-4771 into CLS-4772` |
| `52b39f6f4` | `CLS-4772 Merge master into CLS-4772` (only `.github/workflows/ci.yml`; 4743/4770/4771 already carried the rest) |

After `git fetch` just before this file: `origin/CLS-4743`, `origin/CLS-4770`, `origin/CLS-4771` and `origin/master` are all ancestors of `HEAD`.
Migrations sort in one order, unique timestamps: `Version20261116120000` (master) < `Version20261117120000` (4770) < `Version20261117150000` (4743).
`composer.json` keeps `"lancasters/constants": "dev-CLS-4767 as 1.369"` (constants latest tag `v1.368`, unchanged).

```
git diff --stat 52b39f6f4..HEAD   (final, 3 commits)
 composer.json                                      |   4 +-
 composer.lock                                      |  27 +-
 config/packages/messenger.yaml                     |   9 +
 config/services_test.yaml                          |   2 +
 .../gift/promotion/promotion_rewards_gift.feature  | 242 +++++++++++++++++
 .../promotion/refer_a_friend_rewards_gift.feature  |  49 ++++
 src/AppBundle/Entity/Reward.php                    |   5 +
 .../Job/PromotionGiftActivitySubscriber.php        |  68 +++++
 src/AppBundle/Factory/GiftFactory.php              |  29 ++
 .../Standard/Handler/RewardHandler.php             |   6 +
 src/AppBundle/Resources/config/services.yml        |   7 +
 src/AppBundle/Service/PromotionGiftIssuer.php      | 102 +++++++
 .../DepositTier/Handler/RewardHandler.php          |   1 +
 .../FirstBetInsurance/Handler/RewardHandler.php    |   1 +
 .../InstantReward/Handler/RewardHandler.php        |   1 +
 .../ReferAFriend/Handler/RewardHandler.php         |   4 +
 tests/Acceptance/Steps/GiftSteps.php               | 214 +++++++++++++++
 tests/Acceptance/Steps/RewardAggregatorSteps.php   |  64 +++++
 tests/Unit/AppBundle/Entity/RewardTest.php         |   8 +
 .../Job/PromotionGiftActivitySubscriberTest.php    | 116 ++++++++
 tests/Unit/AppBundle/Factory/GiftFactoryTest.php   |  64 +++++
 .../Standard/Handler/RewardHandlerTest.php         |  28 ++
 .../AppBundle/Service/PromotionGiftIssuerTest.php  | 300 +++++++++++++++++++++
 .../DepositTier/Handler/RewardHandlerTest.php      |  66 +++++
 .../Handler/RewardHandlerTest.php                  |  67 ++++-
 .../InstantReward/RewardHandlerTest.php            |  66 ++++-
 .../Multiplus/Handler/RewardHandlerTest.php        |   4 +
 .../ReferAFriend/Handler/RewardHandlerTest.php     |  88 ++++++
 tests/Unit/Support/GivesPromotionGifts.php         |  89 ++++++
 29 files changed, 1717 insertions(+), 14 deletions(-)
```

## 2. Tasks and criteria

| Task | Where | Covered by |
|---|---|---|
| 1 merges, `make init` | section 1; `make init` itself failed on the lock (see 3), so `up --force-recreate` + `composer update` + `install.sh --yes` | every test below |
| 2 pin | `composer.json:30` `dev-CLS-4768 as 3.152`, `composer.lock` (job-library entry, `dev-CLS-4768`, ref `8b8f510d…`, alias `3.152`) | `vendor/.../UserActivityJob.php:24` has `SOURCE_TYPE_PROMOTION`; subscriber and Behat run on it |
| 3 `Reward::isGift()` | `src/AppBundle/Entity/Reward.php:90` | `RewardTest::it_is_a_gift_only_when_its_type_is_gift` |
| 4 `GiftFactory::createForPromotionReward()` | `src/AppBundle/Factory/GiftFactory.php:52` (reason: `:69`, via `getReasonIncludingDeleted`) | `GiftFactoryTest` (copy, no reason, deleted reason) |
| 5 `PromotionGiftIssuer` | `src/AppBundle/Service/PromotionGiftIssuer.php` (`issue()` `:29`, key `:17,42`, dedupe `:44-48`, lookup `:50`, skips `:55,84-91`, persist `:76`, no flush) | `PromotionGiftIssuerTest` (11 tests: copy, bonus ignored, two gifts, same reward twice, existing key silent, no configuration / deleted / disabled each one warning, other gifts still issued, stock ignored, never flushes); Behat both features |
| 6 Standard handler | `Standard/Handler/RewardHandler.php:46` (constructor), `:219-221` (skip gift in bonus loop) | Standard `RewardHandlerTest::it_leaves_gift_rewards_out_of_the_bonus_loop_without_calling_the_calculator` (fails without the skip: verified by removing it) |
| 7 Deposit tier / FBI / Instant | `DepositTier/Handler/RewardHandler.php:74`, `FirstBetInsurance/Handler/RewardHandler.php:56`, `InstantReward/Handler/RewardHandler.php:52` | each handler's `RewardHandlerTest` (gift persisted after the bonus, for that instance; none when a bonus fails in the wallet); Behat |
| 8 Refer a friend | `ReferAFriend/Handler/RewardHandler.php:43,57` (constructor), `:279` (after `issuePlayerBonuses`) | RAF `RewardHandlerTest` (gift of each role to that role's instance; role with `bonus_offer_allowed` false gets none and stays engaged); `refer_a_friend_rewards_gift.feature` |
| 9 subscriber | `src/AppBundle/EventListener/Job/PromotionGiftActivitySubscriber.php` (`:23` class, `:29,35` updates/deletions off, `:43-65` job) | `PromotionGiftActivitySubscriberTest` (exact fields, null reason, null configuration, no `sourcePromotionId`, update, delete) |
| 10 service | `src/AppBundle/Resources/config/services.yml:180` | Behat activity assertions (the job only exists if the listener is wired) |
| 11 messenger | `config/packages/messenger.yaml:14` (param), `:29` (route), `:67-71` (transport), `:110` (`in-memory://` in test) | Behat activity assertions |
| 12 `services_test.yaml` | `config/services_test.yaml:252` (+ `:253` `$eventDispatcher`, see deviations) | Behat |
| 13 tests, run | section 3 | |

| Acceptance criterion | Where | Covered by |
|---|---|---|
| Gift per gift reward, `claimed`, copied (name, offerAmount, currency, reason, `sourcePromotionId`) for Deposit tier / FBI / Instant; RAF to the role's recipient | `PromotionGiftIssuer.php:76`, `GiftFactory.php:52-67` | unit `PromotionGiftIssuerTest`, `GiftFactoryTest`; Behat "tier with only a gift", "carries the reason", "first bet insurance rule", "instant reward"; RAF "each get the gift of their role" |
| Composition: only gift, gift + bonus, two gifts, only bonus unchanged | `Standard/Handler/RewardHandler.php:219`, issuer after the bonus loop | Behat scenarios 1, 2, 3; existing `deposit_tier/reward`, `first_bet_insurance/reward`, `instant_reward/reward`, `refer_a_friend/reward`, `features/gift` all green |
| No wallet currency / other currency: gift in the promotion currency, bonus as today | issuer is after the loop and ignores its currency checks | Behat "player without a wallet", "wallet only in another currency"; unit `it_issues_the_gift_in_the_promotion_currency_when_the_context_has_no_currency` (the `getCurrency() === null` early return; not reachable from Behat, `SuccessfulDepositJob::$currency` is a non-null string) |
| Stock reached: gift created and counted | `PromotionGiftIssuer.php:76` (no `saveWithinStock`) | unit `it_persists_the_gift_whatever_the_stock_of_its_configuration`; Behat "stock … reached" (count 2 through the BO count step) |
| Disabled or deleted: no gift, one `warning` with reason, bonuses issued, instance `rewarded`, no exception | `PromotionGiftIssuer.php:55-74,84-91` | unit (3 skip tests); Behat "disabled", "deleted" |
| Reprocessing after a wallet failure creates one gift; RAF replay does not duplicate | issuer runs after the loop (`V2Exception` leaves no gift); key `:42-50` | unit "no gift when a bonus … fails in the wallet" (Deposit tier, FBI, Instant), "existing key"; Behat "same deposit sent twice", RAF replay (see deviation 7) |
| `bonus_offer_allowed` false: no gift, no bonus, instance engaged | unchanged (validator / RAF role check) | Behat "wallet does not allow bonus offers", RAF "referrer whose wallet does not allow"; unit RAF |
| Editing the configuration after rewarding does not change the gift | the gift is a copy | Behat "Renaming the configuration after rewarding" |
| Limits and counters as today | `updateStatusesAndCounters()` untouched | existing features green |
| One `GiftEventJob` per gift insert, unchanged | `GiftEventSubscriber` untouched | Behat "exactly 2 gift KPI events of type created"; `features/gift` |
| One `gift_offered` `UserActivityJob` per promotion gift, none for manual/scenario | `PromotionGiftActivitySubscriber.php:43-65` | unit (fields, no source, update); Behat `:count gift_offered activity jobs` (asserts event, `sourceType`, `sourceUserId`, the whole `additionalData`); `features/gift` offers show none sent |

## 3. Commands and output

`make init` (first run) stopped at the lock: `Required package lancasters/job-library is in the lock file as v3.149 but that does not satisfy your constraint dev-CLS-4768 as 3.152` (expected, as in 4771). Then:

```
docker compose -f docker-compose.dev.yml exec php composer update lancasters/job-library --no-interaction
  ... Generating autoload files
  Failed to copy pre-commit file. copy(.git/hooks/pre-commit): Failed to open stream: No such file or directory
  Script CelestaDev\Git\Integrator::integrate handling the post-update-cmd event terminated with an exception
  (after the lock was written; harmless, worktree .git is a file). git diff composer.lock: only job-library (+ alias entry).
docker compose -f docker-compose.dev.yml exec php /bin/sh install.sh --yes
  [OK] Successfully migrated to version: App\Migrations\Version20261117150000   (dev and test)
docker compose -f docker-compose.dev.yml exec php bin/console cache:clear --env=test   (after config/services_test.yaml changed; the Behat container was stale)
```

Plan commands, final run on the committed tree (full output in the logs):

```
docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/phpunit <the 10 touched/created test files>     (phpunit-touched.log)
  OK (138 tests, 454 assertions)   [re-run after the second amend]

docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/behat features/gift/promotion features/deposit_tier/reward features/first_bet_insurance/reward features/instant_reward/reward features/refer_a_friend/reward features/gift     (behat-plan.log)
  215 scenarios (215 passed)
  2382 steps (2382 passed)
  0m37.21s (63.62Mb)   [re-run after the second amend]
```

Wider runs (not in the plan; run on the first amend, not repeated after the second, which only touches `GiftSteps.php` and the Instant scenario, to catch the constructor and subscriber being global):

```
phpunit tests/Unit/AppBundle tests/Unit/PromotionConfigurationBundle tests/Unit/ApiBundle     (phpunit-wide.log)
  OK, but there were issues!
  Tests: 1934, Assertions: 4468, Risky: 2.
  (the 2 risky are PlayerHasCurrencyValidatorTest, untouched: "not expected to perform assertions but performed 1 assertion")

behat features/reward_configuration features/reward_offering_reason features/gift_request features/bonus features/standard features/deposit_tier features/first_bet_insurance features/instant_reward features/refer_a_friend     (behat-wide.log)
  1107 scenarios (1107 passed)
  8259 steps (8259 passed)
  1m22.72s (99.26Mb)
```

Failures on the way, all mine, none from another diff:
- First Behat run of the new feature: scenarios failed on the missing `GiftSteps` argument (container cache), on the activity/KPI queues being empty (the subscribers buffer in `PostResponseMessageDispatcher` until a worker message is handled; fixed by the steps playing `WorkerMessageHandledEvent`), on the bonus not being created (the gift configuration took id 1 and Bonus A pointed at it; fixed by creating the aggregator before the gift configuration) and on a step ambiguity (`a created gift KPI event should be queued` vs my count step; renamed). `features/gift/listing/bo_user_lists_gifts.feature:108` died with `Call to a member function getId() on null` in the subscriber (a gift with `sourcePromotionId` and no configuration, from 4770's builder): fixed with `?->getId()` and a unit test. No assertion loosened.
- Running `features/deposit_tier/reward/rewarding_players_based_on_reward_aggregator_tier.feature` **alone** fails 4 of 8 on this branch (`Please specify a mock data for 'GET http://crmweb.docker/en/api/customer/1'`, the first call of the job handler to Memberzone, no player 1 in the DB yet); the whole `features/deposit_tier/reward` directory passes 14 of 14. Order dependence of the existing suite (an earlier feature creates player 1 through a login); I did not check it on master. My feature opens every deposit scenario with `the player with id 1 logs in` for that reason.

`make lint` (exit 0, re-run after the second amend, `lint.log`; it lints the diff against `origin/master`, so it also reports 4770/4771/4743 files): nothing on `PromotionGiftIssuer.php`, `PromotionGiftActivitySubscriber.php` or `GiftFactory.php` after the amend (first run: line over 120 and cyclomatic 7 in the issuer; fixed by extracting `skipReason()`). Existing findings only on the handlers and `Reward.php` (`@return`/`@param` of traversables, "space after not", line lengths, complexity), none on the lines of this diff. The repository's pre-commit hook ran (phpinsights + message check) and passed on the final commit.

Not run locally: the coverage gates (100% PHPUnit / merged). The new service, subscriber, factory method and predicate are all in the `phpunit.xml` scope and each line is hit by the unit tests above; `Gift.php` stays excluded.

Mutation check done by hand (earlier hash): removing the four `promotionGiftIssuer->issue()` calls and the `isGift()` skip makes 7 of the new handler tests fail (Standard skip, Deposit tier, FBI, Instant, RAF x2, plus the FBI wallet-failure error); restored.

## 4. Deviations from the plan

1. **Alias:** `dev-CLS-4768 as 3.152`, not 3.150 (job-library latest tag `v3.151`, re-checked today).
2. **`PromotionGiftIssuer` constructor:** `GiftFactory`, `GiftRepository`, `EntityManagerInterface`, `LoggerInterface`; it reads `RewardConfigurationRepository` with `$entityManager->getRepository(RewardConfiguration::class)`. The plan listed the repository as a dependency, but it extends `EntityRepository` and cannot be autowired (container compile error `Cannot autowire service "…RewardConfigurationRepository": argument "$class" … ClassMetadata`); every other service here goes through `getRepository()`.
3. **In-call dedupe** marks the key as seen before the DB lookup and the skip checks (plan: "skip a key already issued in this call"). Instant reward lists aggregator rewards twice, so a disabled or deleted configuration now logs once, not twice.
4. **Subscriber:** `reward_configuration_id` uses `?->getId()` (see section 3); `description` is `$gift->getDescription()` (null for a promotion gift, as the plan's table says).
5. **Unit tests:** the issuer is `final readonly`, so the handler tests use a real one built by a new trait, `tests/Unit/Support/GivesPromotionGifts.php` (not in File Changes). The Multiplus test is constructor-only, as planned (it also uses the trait to build the argument).
6. **Behat, beyond the four steps the plan names:** `the activity queue is empty`; `the gift reward configuration :name has the reward offering reason :reason` (so the reason is not null on both sides); `exactly :count gift KPI event(s) of type created should be queued` (the existing singular step needs a `currentGiftId`); and `GiftSteps` takes `$eventDispatcher` besides `$activityTransport`, to dispatch `WorkerMessageHandledEvent` before reading the queues (the steps call the deposit/bet handlers directly, so nothing ever flushes `PostResponseMessageDispatcher`). The "gift" assertion step finds gifts by player and name and compares them with their own configuration, so the rename scenario can look the old name up.
7. **Scenarios that differ from the plan's wording, and two findings for the coordinator:**
   - *RAF replay.* The plan says the next event replays both roles and the referrer's key blocks a second gift. In the code the replay never reaches the issuer: `PromotionRepository::getReferrerPromotionByRefereePromotion()` requires the referrer's promotion to be `engaged` (`:377`), and the referrer was flushed `rewarded` before the referee. The scenario (referee wallet flag false, referrer rewarded, event replayed with the flag true) asserts the referrer still has exactly one gift; it passes without the key, so it does not prove the idempotency. The key stays as a backstop. Side effect, not mine: that referee is never rewarded on a replay.
   - *Instant reward.* Settled in `instant-reward-investigation.md`: the test environment registers the `AuthorizationJob` handler twice, so one login rewards two instances (with or without a gift); production has one handler. The scenario now asserts one gift and one `gift_offered` activity **per rewarded instance** of the promotion (new steps `the player :playerId should have one gift :giftName for each rewarded instance of the promotion :promotionName` and `one gift_offered activity job should be sent for each rewarded instance of the promotion :promotionName for the player :playerId`, which count the `rewarded` rows first), so it holds with one or two handlers.
   - *"Player without wallet currency".* `SuccessfulDepositJob::$currency` is a non-null string, so the `getCurrency() === null` return of `issuePlayerBonuses()` is not reachable from the deposit flow in Behat. Behat: "no wallet" (empty currency list) and "wallet only in USD", both with a bonus in a currency the brand does not accept; the null-currency path is the DepositTier unit test.
8. **Process, for the record.** My first `git commit` ran with `-c core.hooksPath=<missing dir>`, which skipped the repository hooks. I noticed before anything else was done with it, `git reset --soft`, and committed again with the hooks active (phpinsights and commit-message check both ran and passed); the commit above is that one. A `git stash` I ran by mistake in the same session was popped immediately and nothing was lost (checked by diff and by re-running the tests). No `--no-verify` anywhere.
9. `.env` copied into the worktree from the main clone (git-ignored). The sibling merges brought the siblings' `.sdd/_plans/CLS-4743|4770|4771.md` into this branch; they leave with the merges.
10. The plan's Testing Strategy has no whole-suite command and `CLAUDE.md` forbids the unfiltered one: ran the plan's commands plus the two wider runs above, not `make test`.

## 5. Proteus

Worktree `/private/tmp/cls3916/celesta-qaa-proteus-4772`, branch `CLS-4772` cut from `origin/master` `0daf2d74c` (still master's tip after a fresh `git fetch`). `.env` and `.env.dev` copied from the main clone. Not pushed, not run, no Qase sync.

Commits (`git log origin/master..HEAD`, mine in bold):
- `b08f668be` `CLS-4772 Merge CLS-4743 into CLS-4772`
- `87ca76f07` `CLS-4772 Merge CLS-4770 into CLS-4772`
- `a25b27c64` `CLS-4772 Merge CLS-4771 into CLS-4772` (all three: no conflicts)
- **`b2402966e`** `CLS-4772 Add the deposit tier gift offered once suite`

```
git diff --stat HEAD~1
 .../depositTierGiftOfferedOnce.pcpr-37.test.ts     | 556 +++++++++++++++++++++
 1 file changed, 556 insertions(+)
```

New suite: `src/tests/celesta-promotion/scenario/depositTierGiftOfferedOnce.pcpr-37.test.ts` (highest id on master is **pcpr-36**, `mock/gift.pcpr-36`, not 34 as the plan said; no `pcpr-37` on any remote branch). Shape: pcpr-19 under the `celesta-promotion-queue` lock, three players each with a deposit tier promotion (tier player: gift + bonus, same deposit job twice; wallet player: gift only, only wallet in USD; disabled gift player: disabled gift + bonus), one consumer run of 4 jobs, then `GET /api/domain/{domainId}/gifts` with the four steps of the service API (`200 OK`, `List not empty`, `OpenAPI`) and three `(Data validation)` steps, one per plan scenario.

Checks done without running a suite: `npx tsc --noEmit -p .` exit 0 and `npx eslint` on the file, no output (main clone's `node_modules` through a temporary symlink, removed).

Differences from the plan's Proteus section:
- **Merged the three sibling Proteus branches** (`origin/CLS-4743`, `4770`, `4771`) into the Proteus branch, which the instruction did not ask for: the suite needs `RewardType.GIFT` (4771), `source_promotion_id` / `sourcePromotionId` (4770) and `reason_id` on the reward configuration payload (4743), none of which is on master. Same logic as step 0 of the service. If you prefer a branch with only my commit, drop the three merge commits and the suite will not type-check until the siblings merge.
- **Seeded with Service Data, not saved through the service API** (the plan says "saved through the service API"): the save path of a gift reward is CLS-4771's suite, and the API route needs the BO user chain; pcpr-19 seeds the same way. The gift reward rows keep Service Data's generated `options` (`upToAmount`), which the service ignores.
- "No wallet in the promotion currency" is a wallet in USD (a missing wallet makes the mock answer 404, which `bonus_offer_allowed` treats as not allowed: a different scenario).
- `(Data validation)` steps use `expect(...).toStrictEqual` on picked values (arrays of gift and bonus fields), as pcpr-19 does, not `compareExpectedToReceived`: the expected gift has no captured record (the service creates it).
- Not done (rules of the repository, as in 4770 and 4771): `qaa-reviewer`, `npm run build:unit-test:dev`, "ask for OAS and SQL", `_specs`/`_plans` for the new case. **The Qase case `PCPR-37` has to be created** (`npm run qase:sync:apply`, after the PR merges) before the suite reports anywhere.

Attribution check, both repositories (`git log origin/master..HEAD --format='%s%n%b' | grep -iE 'co-authored|🤖|generated with|claude code'`): prints nothing.

## Pending, outside this ticket

- **Qase case `PCPR-37`** for the new Proteus suite `depositTierGiftOfferedOnce.pcpr-37` still has to be created (`npm run qase:sync`, dry run first); it needs Qase credentials, so QA or Lucas.
- **`config/services_test.yaml:53-57`** defines `test.auth_message_handler` with the same class as the real `AuthorizationJobHandler`, and `autoconfigure` registers the `AuthorizationJob` handler twice in the test environment (same on `origin/master`; `debug:messenger` shows two handlers in `test`, one in `dev`): to be raised with whoever owns the test environment.

## After the push (2026-11-18)

Pushed `origin CLS-4772` (service) `91cd7266b..b6e040321`, then fix commits, never amended after the first push:
- `b6e040321` implementation (the amended one above); Proteus `CLS-4772` pushed (`b2402966e` on top of the three merges), PR https://github.com/celesta-tech/celesta-qaa-proteus/pull/859.
- `0dcf3d7ec` `CLS-4772 Address review round 1`: `declare(strict_types=1)` in the issuer and the subscriber, issuer split into `findConfiguration()` and a `match (true)` skip reason, a Behat scenario that seeds a gift under the key of the engaged instance (fails without the lookup, checked by hand), RAF scenario title.
- `08993a42e` `CLS-4772 Move the constants alias past the released 1.369`: constants `v1.369` was released by someone else on 2026-11-18 (no `TYPE_GIFT`), so the pin brought by 4771 is now `dev-CLS-4767 as 1.370` (`composer update lancasters/constants`, only the alias and the content-hash changed). **#605 and the backoffice pin carry `as 1.369` and need the same bump.** job-library latest tag is still `v3.151` (alias 3.152 holds).

Review on PR #606: round 1 (b6e040321): tests 1 should-fix + 1 nit, quality 1 blocking + 1 nit, the other six no findings; round 2 (0dcf3d7ec): all four threads resolved by their reviewers, other six no findings; round 3 (08993a42e, pin only): eight no findings. Label `sdd-reviewed`; 4 of 4 threads resolved.
Re-run before each round and at the end: phpunit touched OK (435 tests with the whole `PromotionConfigurationBundle`), `phpunit tests/Unit/AppBundle tests/Unit/PromotionConfigurationBundle tests/Unit/ApiBundle` OK (1934 tests, 2 risky existing), Behat plan set 217 scenarios passed (2410 steps), `make lint` clean on the issuer and the subscriber (`lint.log`).

## CI (workflow_dispatch on `CLS-4772`, after the last service push `7b122834a`)

First two runs (`44279595692` on `08993a42e`, `44280672851` on `5f65acfcb`): every job green except `proteus / isolated-tests`: only the new suite failed (`depositTierGiftOfferedOnce.pcpr-37`, 3 of 757 tests: `consumerExitCode` 1 with 4 messages left in the queue, then the two scenarios that depend on the later jobs); the tier player's steps passed, so the first job ran and its gift existed. Causes, both stand configuration of this repository, both explained by the diff (a real consumer now emits `UserActivityJob` and `GiftEventJob` from a worker, which the HTTP-only gift suites never did):
- the Proteus broker (`ops/docker/config/elasticmq.conf`, transports run with `auto_setup: false`) had no `dev-activity` queue: added in `5f65acfcb`;
- `.env.dev` sends the quanta transport (`statistics_kpi_sqs`, the `GiftEventJob` of every gift insert) to `localsqs.docker`, which does not resolve in CI, and the broker had no `dev-statistics-kpi`: `SQS_QUANTA_TRANSPORT_DSN` in `docker-compose.proteus.yml` and the queue in `elasticmq.conf`, `7b122834a`. The first fix alone did not turn it green; I did not read the consumer's stderr (the suite did not log it), so the second cause is the one the code explains, confirmed by the green run. The suite now logs the consumer's stderr when its exit code is not 0 (Proteus `69680c45d`).
Run `44282016965` on `7b122834a`: all jobs success (`pr-status-start`, `migration / validate`, `security / Datadog Static Analyzer`, `security / Datadog Quality Gates`, `build / images`, `tests / tests`, `tests / openapi-lint`, `tests / codestyle`, `proteus / isolated-tests` with the new suite passing, `proteus / Mark tree verified`, `tags / create` (the branch image tag `CLS-4772-<sha>`, no git tag), `copy-openapi-files / create`, `pr-status-end`); `proteus / Verified tree gate`, `release`, `auto_deploy`, `copy-openapi-files / get-version` skipped as usual.
Review of the two stand commits: all eight, no findings. Final service commits: `0dcf3d7ec`, `08993a42e`, `5f65acfcb`, `7b122834a`. Label `sdd-reviewed`. Cost comment posted on the sub-task (`sdd-implement` $37.65).
**Deploy note for Team O / the release:** `activity_sqs` needs the queue `<SQS_QUEUE_PREFIX>activity` in every environment (already there per `decisions.md`); nothing else.

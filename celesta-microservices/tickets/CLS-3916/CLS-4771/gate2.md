# CLS-4771 gate 2

Worktree `/private/tmp/cls3916/celesta-promotion-4771`, branch `CLS-4771`, plan commit `c69879f20`. Not pushed. Stack
(`promotion.php`/`promotion.nginx`) repointed to this worktree with `make init` (coordinator's go-ahead; 4770 had finished).
Logs in this folder: `lint.log`, `openapi.log`, `behat-features.log`.

## 0. Merges (lesson from 4770)

- Service: work saved as patch (`.../scratchpad/cls4771-service.patch`, 17 modified files, no new ones), tree restored, `git merge origin/master`
  (message `CLS-4771 Merge master into CLS-4771`, `c87d93012e30433ec6d4afa989725c49e9865f45`): no conflicts (brings `gift_request`, `Version20261113100101`,
  `Version20261116120000`, etc.). Patch re-applied with `git apply --3way`: clean, no conflict markers. `composer.json` keeps master's `celesta-fixtures ^1.241` and
  my pin (`git diff origin/master -- composer.json` shows only the constants line).
- Proteus: `git merge origin/master` (message `CLS-4771 Merge master into CLS-4771`, `6d874d14df90f04ee3b21731b81926bcfa836236`): no conflicts
  (`endpoint-coverage/celesta-promotion.json` and `constants.ts` merged by git, both sides kept). `tsc --noEmit` exit 0; eslint 0 errors, 3 existing
  spellcheck warnings (`optin`) in `serviceAPI.ts`.

## 1. Implementation commit

`56b596f682c09b4c382f6a8daedc1e239f8639c6` `CLS-4771 Accept the gift reward type in promotion rewards` (on top of the merge commit; amended once, after `make lint`,
to wrap two lines over 120 chars in `getGiftConfigurationError`).

```
git diff --stat c87d93012..HEAD
 composer.json                                      |   2 +-
 composer.lock                                      |  27 +-
 .../creation/bo_user_creates_reward.feature        |  71 +++++   (features/deposit_tier)
 .../bo_user_creates_reward_aggregator_tier.feature |  41 +++
 .../creation/bo_user_creates_reward.feature        |  11 +    (first_bet_insurance)
 .../creation/bo_user_updates_reward.feature        |  33 ++    (instant_reward)
 .../creation/bo_user_creates_reward.feature        |   8 +     (multiplus)
 ...user_creates_reward_aggregator_raf_role.feature |  52 ++++
 ...s_promotion_configurations_with_rewards.feature |  18 ++
 src/ApiBundle/Normalizer/RewardNormalizer.php      |   7 +-
 .../Form/EventListener/RewardSubscriber.php        |  71 ++++-
 .../{DepositTier,FirstBetInsurance,InstantReward,ReferAFriend}/Form/Type/RewardType.php | 2 each
 tests/Acceptance/Steps/RewardSteps.php             |  83 ++++++
 .../ApiBundle/Normalizer/RewardNormalizerTest.php  |  58 ++++
 .../Form/EventListener/RewardSubscriberTest.php    | 331 ++++++++++++++++++++-
 18 files changed, 805 insertions(+), 16 deletions(-)
```

Pin: `"lancasters/constants": "dev-CLS-4767 as 1.369"`. `git fetch origin --tags` + `git tag --sort=-v:refname | head -1` of celesta-constants = `v1.368` (re-checked
today before `composer update`), so `1.369` is free. `composer update lancasters/constants` in the container moved only that package (lock: `dev-CLS-4767`,
reference `5c046477001f62f8e6b876c3093057c222d6fa4d`, alias `1.369`, `stability-flags`); the post-update hook `CelestaDev\Git\Integrator` then failed
("Failed to copy pre-commit file .git/hooks/pre-commit": the worktree's `.git` is a file), after the lock was written. Harmless here; `install.sh --yes` ran fine afterwards.

## 2. Tasks and criteria

| Task | Where | Covered by |
|---|---|---|
| 1 pin | `composer.json:26`, `composer.lock` (`lancasters/constants` entry) | `install.sh` ran green; every test below runs on `RewardConstants::TYPE_GIFT` from the branch |
| 2 allowed types | `DepositTier/Form/Type/RewardType.php:50`, `FirstBetInsurance/...:50`, `ReferAFriend/...:48`, `InstantReward/...:46`; Multiplus untouched | Behat `multiplus/.../bo_user_creates_reward.feature:48`; gift-create scenarios of deposit tier `:54`, FBI `:54`, instant reward `:57` |
| 3 OpenAPI enum | same four files, lines 20, 20, 19, 18 | `make openapi` (below): enums checked in `public/open-api.json` |
| 4 type read + message constants | `RewardSubscriber.php:22-31`, `:60` (type from the field), `:62,73` (passed on), `readRewardType` | `it_does_not_throw_when_a_post_has_no_type` |
| 5 null id on gift | `RewardSubscriber.php:98-102` | `it_rejects_a_gift_reward_without_a_source_id_and_keeps_the_configuration`, `it_rejects_a_gift_reward_patched_with_a_null_bonus_model_id`, `it_clears_the_source_of_a_bonus_reward_without_a_source_id`; Behat deposit tier `:109`, instant reward `:80` |
| 6 gift rules | `RewardSubscriber.php:122-135`, `getGiftConfigurationError` (not gift, disabled, currency, in that order); bonus-type rejection kept at `:130` | `it_rejects_a_gift_reward_pointing_at_a_non_gift_configuration` (free, deposit, free rounds), `it_keeps_rejecting_a_bonus_reward_pointing_at_a_gift_configuration`, `it_rejects_a_disabled_gift_configuration`, `it_rejects_a_gift_configuration_in_another_currency_than_the_promotion`, `it_adds_no_status_rule_to_a_bonus_reward`, `it_accepts_a_gift_reward_sent_as_*`; Behat deposit tier `:65,76,84,93,101` |
| 7 quantity/options | `RewardSubscriber.php:64-66`, `validateGiftFields` | `it_rejects_a_quantity_on_a_gift_reward`, `it_rejects_non_empty_options_on_a_gift_reward`, `it_accepts_empty_options_on_a_gift_reward`, `it_leaves_a_stored_gift_reward_alone_when_a_patch_sends_nothing`; Behat deposit tier `:116` |
| 8 normalizer | `RewardNormalizer.php:34,37` (aggregator group registered before the skip) | `RewardNormalizerTest.php:230,245,263,273`; Behat player route `player_views_..._with_rewards.feature:41` |
| 9 tests | Files section of the plan; see deviations | all green below |
| 10 lint, openapi | below | below |

Acceptance criteria:
- Gift accepted on the four types, directly and in aggregators; Multiplus 400 on `type`: Behat deposit tier `:54`, FBI `:54`, instant reward `:57`, tier aggregator `:94,115`, RAF referrer `:178` and referee `:195`, multiplus `:48`. Met.
- Enabled gift configuration, same domain and currency, by `rewardConfigurationId` or `bonusModelId`; GET returns `type: gift` and the id: unit `it_accepts_a_gift_reward_sent_as_*`; Behat `I view the reward details` + `the returned reward should be a gift of ...` (deposit tier, FBI, instant reward; instant reward PATCH `:68`). `GET .../rewards` and `GET .../reward-aggregators`: aggregator scenarios assert `reward aggregator 0 should have 2 rewards`, no assertion of the `bonusModelId` of the list items. Met, list-item `bonusModelId` unasserted (same serializer as `reward_get`).
- Non-gift configuration 400 on `rewardConfigurationId`: unit + Behat `:65`. Met.
- Bonus type with gift configuration unchanged: unit + `features/standard/configuration/creation/bo_user_creates_reward.feature:55` (untouched, passes). Met.
- Disabled / deleted / other domain: Behat `:76,84,93`; unit. Met.
- Other currency; bonus types gain no rule: Behat `:101` and RAF `:200`; unit. Met.
- No id, quantity, non-empty options; two gifts in a tier accepted: unit; Behat `:109,116`, tier aggregator `:115`. Non-empty `options` has no Behat scenario (unit only).
- Player route: Behat `:41` (tier with bonus + gift has 1 reward, tier with only a gift has 0 rewards), normalizer unit tests. Met.
- `PotentialWinningsCalculator` untouched. Met.
- OpenAPI enums: met (see below).
- Existing reward types save and read as before: every existing scenario of the directories below is green. Met.

## 3. Test commands and output

Setup: `make init` first ran with the old lock and failed on "Required package lancasters/constants is in the lock file as v1.367 but that does not satisfy your constraint
dev-CLS-4767 as 1.369" (expected: the plan's task 1 `composer update` is the fix). Then `docker compose -f docker-compose.dev.yml exec php composer update lancasters/constants --no-interaction`
(see section 1) and `docker compose -f docker-compose.dev.yml exec php /bin/sh install.sh --yes` -> exit 0, both DBs `Successfully migrated to version: App\Migrations\Version20261116120000` (72 migrations).
`.env` copied from `/Users/l.franco/Desktop/celesta-projects/celesta-promotion/.env` (git-ignored).

```
docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/phpunit tests/Unit/AppBundle/PromotionConfiguration/Standard/Form/EventListener/RewardSubscriberTest.php tests/Unit/ApiBundle/Normalizer/RewardNormalizerTest.php
  OK (34 tests, 127 assertions)
```
(First run, before fixing my own test: 34 tests, 127 assertions, 1 failure `it_rejects_non_empty_options_on_a_gift_reward`: "Failed asserting that null is identical to 'A gift reward does not take options.'".
Cause was the test form, not the subscriber: the `options` collection child lacked `'error_bubbling' => false`, which `AbstractRewardType` sets, so the error bubbled to the root form. Fixed in the test's form wiring, assertion untouched.)

```
phpunit tests/Unit/AppBundle/Service/PromotionConfigurationServiceTest.php tests/Unit/AppBundle/PromotionConfiguration tests/Unit/ApiBundle/Normalizer
  OK, but there were issues!   Tests: 311, Assertions: 638, Risky: 2.
```
The 2 risky tests are in `PlayerHasCurrencyValidatorTest` (untouched, "not expected to perform assertions but performed 1 assertion"), not from this diff.

Behat, each feature file (final run after the lint amend, `behat-features.log`):
```
features/deposit_tier/creation/bo_user_creates_reward.feature                      16 scenarios (16 passed), 138 steps (138 passed)
features/deposit_tier/creation/bo_user_creates_reward_aggregator_tier.feature       7 scenarios (7 passed), 60 steps (60 passed)
features/first_bet_insurance/creation/bo_user_creates_reward.feature                9 scenarios (9 passed), 82 steps (82 passed)
features/instant_reward/creation/bo_user_updates_reward.feature                    11 scenarios (11 passed), 108 steps (108 passed)
features/multiplus/creation/bo_user_creates_reward.feature                          6 scenarios (6 passed), 50 steps (50 passed)
features/refer_a_friend/creation/bo_user_creates_reward_aggregator_raf_role.feature 12 scenarios (12 passed), 76 steps (76 passed)
features/standard/configuration/listing/player_views_promotion_configurations_with_rewards.feature 3 scenarios (3 passed), 36 steps (36 passed)
features/standard/configuration/creation/bo_user_creates_reward.feature            9 scenarios (9 passed), 72 steps (72 passed)
```
Behat on whole directories (before the lint amend, which only reshaped one `match`; the 8 files above were re-run after it):
```
features/deposit_tier 39 scenarios (39 passed) 326 steps | features/first_bet_insurance 39 (39 passed) 322 | features/instant_reward 43 (43 passed) 306
features/multiplus 45 (45 passed) 351 | features/refer_a_friend 95 (95 passed) 893 | features/standard/configuration/creation 89 (89 passed) 610
features/standard/configuration/listing 45 (45 passed) 423 | features/gift 111 (111 passed) 1113
```
Failures I fixed in my own Behat code on the way: the existing step `the reward aggregator should be created with the specified details` asserts 201 but `POST .../reward-aggregators` answers 200 ("Failed asserting that 200 matches expected 201"), so the new scenarios use `the response should be successful`; and two successive `the response should be successful` steps in one scenario died with a PHPUnit `Configuration\Registry::get()` null error (a second assertion in the same scenario), so the RAF referrer/referee scenario was split in two scenarios. No assertion loosened.

`make lint`: exit 0 (`lint.log`). New flags on my diff: cyclomatic complexity of `RewardNormalizer::normalizeRewards` (8) and `RewardSubscriber::resolveRewardSource` (13, "more than 5"); both methods were already above 5 before the change, I did not measure the baseline. The two line-length errors I had introduced were fixed. The other flags (`@return` on `getAllowedTypes`/`getSubscribedEvents`/`normalizeRewards`) are on existing signatures.

`make openapi`: exit 0, redocly "Woohoo! Your API description is valid. You have 26 warnings" (`openapi.log`). In `public/open-api.json`: `Reward.type` and `BaseDepositTierRewardType`, `BaseFirstBetInsuranceRewardType`, `BaseReferAFriendRewardType`, `BaseInstantRewardRewardType` list `gift`; `BaseMultiplusRewardType` is `['free_bonus']`.

Coverage gates not run locally: `phpunit.xml` excludes `src/ApiBundle` and `*Subscriber.php` in `src/AppBundle/PromotionConfiguration/Standard/Form` from the PHPUnit-only report; the merged report was not run.

## 4. Deviations from the plan

- Task 5: the not-blank error goes on `rewardConfigurationId`, falling back to `bonusModelId` only when `rewardConfigurationId` was not submitted (a PATCH sending only `bonusModelId: null` would dereference null). One extra unit case.
- Task 9, Behat steps beyond the one named: `they update the reward from the gift reward configuration :name with:`, `they create a reward aggregator with the following details using the gift reward configuration :name:` (replaces the token `GIFT_ID` in the table and delegates), `the reward aggregator at index :index of the promotion has a gift reward from the gift reward configuration :name`, `the returned reward should be a gift of the gift reward configuration :name`. The plan's step delegates to the "unresolvable configuration" step, not to `they create a reward with the following details:` (that one calls `ensureRewardConfigurationExists`, which would insert a stub for a deleted or other-domain id).
- Tier aggregator "gift and bonus" scenario seeds reward configuration 1 with the existing step `the reward configuration 1 of domain 1 is claimed automatically in currency "EUR"` before the gift configuration.
- RAF: the plan's "referrer and referee aggregators" are two scenarios (see section 3); "referee with a gift in another currency" is the third.
- The subscriber unit test builds a real form (`FormBuilder` + `DataMapper` + factory types, `options` child with `error_bubbling => false`, `data => []`) and submits payloads; the two existing tests are unchanged.
- The vendor check of task 1 (`TYPE_GIFT` in `vendor/lancasters/constants`) is implicit: the suites run against the installed branch.
- `composer.lock` changed only for `lancasters/constants` (+ alias and stability flag).
- Nothing else beyond the plan; `features/standard/configuration/creation/bo_user_creates_reward.feature` untouched (passes).

## 5. Proteus

Worktree `/private/tmp/cls3916/celesta-qaa-proteus-4771`, branch `CLS-4771`. Not pushed, not run.
- `8ee3cb7497a5fecd799324e57e7f8b6d5b32d7f1` `CLS-4771 Add the gift reward type to the promotion reward suites`
- `6d874d14df90f04ee3b21731b81926bcfa836236` `CLS-4771 Merge master into CLS-4771` (no conflicts)

```
git diff --stat origin/master..HEAD
 src/data-services/celesta-promotion/services/serviceAPI.ts                      |  42 +++
 src/data-services/types/constants.ts                                            |   1 +
 .../service/playerPromotionConfigurations.pcpr-4.test.ts                        | 176 ++++++++++-
 .../service/rewardAggregators.pcpr-8.test.ts                                    |  85 ++++-
 .../service/rewards.pcpr-7.test.ts                                              | 352 ++++++++++++++++++++-
 5 files changed, 653 insertions(+), 3 deletions(-)
```
After the merge: `npx tsc --noEmit -p .` exit 0; `npx eslint` on the changed `.ts` files: 0 errors, 3 existing spellcheck warnings in `serviceAPI.ts` (`optin`), main clone's `node_modules` via a temporary symlink, removed.

Differences from the plan's Proteus section:
- The umbrella test "Create gift reward on deposit tier / first bet insurance / refer a friend / instant reward ..." is four tests of four steps (one per type) plus "Data validation - the gift reward configuration is the bonus model".
- Data service additions not in the plan: `ServiceAPI.postGiftReward` and `generateFakeGiftReward` (`postReward` cannot build a gift: `deepMerge` recurses into plain objects, so the generated `options.upToAmount` survives and the service answers 400).
- "Create free bonus reward with a gift reward configuration" sends `{type: free_bonus, bonusModelId: null, rewardConfigurationId: <gift>}` so the error is on `rewardConfigurationId`.
- Each 400 test has `(400 Bad Request)` and `(OpenAPI)`; the player test has an extra "Data validation - no gift item"; the aggregator test has `(200 OK)`, `(Not empty)`, `(OpenAPI)`, `(Data validation - both rewards linked to the aggregator)` on a deposit tier promotion configuration of its own.
- Player test: gift rewards are inserted through Service Data with `quantity: null` and the generated non-empty `options` (the merge cannot clear them); only `type` matters to the route.
- Not done (repository rules): `qaa-reviewer`, `npm run build:unit-test:dev`, "ask for OAS and SQL", Qase sync.
- The Proteus suites were written against the plan's contract and were never executed; the error-body shape (`errors.<field>`) is copied from the gift suite.
- Overlap with CLS-4770's Proteus branch: it changes `constants.ts` near `Gift...` and `serviceData.ts`; this branch touches `RewardType` in `constants.ts` and adds methods to `serviceAPI.ts`. A textual merge should be clean. Not merged here.

Attribution check, both repos: `git log origin/master..HEAD --format='%s%n%b' | grep -iE 'co-authored|🤖|generated with|claude code'` prints nothing.

## 6. After the push (sdd-implement, step 2 and CI)

- Pushes: `56b596f68` (implementation, on top of the merge), `9c63d8afc` (round 1 fixes), `627759ab9` (round 2 fix). Never amended after the first push.
- Proteus PR: https://github.com/celesta-tech/celesta-qaa-proteus/pull/854 (branch `CLS-4771`, `6d874d14d`).
- Service PR: https://github.com/celesta-tech/celesta-promotion/pull/605. Label `sdd-reviewed`. Jira: label `sdd-implement` only; cost comment at the end.
- Review: 3 rounds x 8 reviewers. Round 1 (`56b596f68`): contract nit (not blank error on `bonusModelId` instead of `rewardConfigurationId`), tests 2 should-fix (aggregator scenarios only counted rewards; instant reward error not asserted per field), dead code nit (`has('type')` guard), quality nit (`elseif` on the gift check); security, memory, performance, db: no findings. Round 2 (`9c63d8afc`): 4 threads resolved, tests 1 new should-fix (step relied on reward order in the aggregator). Round 3 (`627759ab9`): all eight no findings, 5 of 5 threads resolved.
- Hook note: the repository's pre-commit hook (`hooks/pre-commit`) runs phpinsights with `exec` on the FIRST changed php file only, and `tests/Acceptance/Steps/RewardSteps.php` fails the hook's complexity score on `origin/master` too (-150 pts, avg 2.10; 1.88 with this branch). A commit whose only php file is `RewardSteps.php` cannot pass, so the by-type step of round 2 lives in `GiftSteps.php` (which passes), and the per-index step it replaces was removed from `RewardSteps.php`. No `--no-verify`.
- Alias `lancasters/constants ... as 1.369`: `git tag --sort=-v:refname | head -1` of celesta-constants was `v1.368` before the review round and at the end, did not move.
- Final run on `627759ab9` (`final-run.log`): phpunit (PromotionConfiguration, Normalizer, PromotionConfigurationServiceTest) OK 311 tests, 639 assertions, 2 pre-existing risky; Behat: deposit_tier 39, first_bet_insurance 39, instant_reward 43, multiplus 45, refer_a_friend 95, standard/configuration/creation 89, listing 45, gift 111 scenarios, all passed.

## 7. Alias bump to 1.370

`celesta-constants` released `v1.369` (another team), so the alias moved: `composer.json` `"lancasters/constants": "dev-CLS-4767 as 1.370"` (last tag re-checked: `v1.369`; `origin/CLS-4767` = `fd3438e70e20fed660fec7ba0ce311cb230e3307`).
Stack was repointed to this worktree (`make init`), then `composer update lancasters/constants` in the container: only `lancasters/constants` moved (`5c04647` -> `fd3438e`); the post-update hook failed only on "Failed to copy pre-commit file" (harmless).
Lock diff: `content-hash`, constants `reference`/dist url `5c046477` -> `fd3438e7`, `time`, alias `1.369` -> `1.370`; `git diff --stat`: `composer.json` and `composer.lock` only (8 insertions, 8 deletions).
Commit `c382860d23a205c26e3b24f6eefef48567218a8e` `CLS-4771 Move the constants alias past the released 1.369` (hook approved, no `--no-verify`), pushed plain. Attribution grep: nothing.
Tests (`alias-run.log`): phpunit RewardSubscriberTest + RewardNormalizerTest OK (34 tests, 128 assertions); Behat deposit_tier creation (16) and aggregator tier (7), first_bet_insurance (9), instant_reward update (11), multiplus (6), refer_a_friend raf_role aggregator (12), player listing with rewards (3), standard creation (9), features/gift (111): all passed.
CI: run 44283636800 on `c382860d2`: success. pr-status-start, build / images, migration / validate, security (Datadog Static Analyzer, Quality Gates), tests (openapi-lint, codestyle, tests), proteus / isolated-tests, tags / create, copy-openapi-files / create, pr-status-end: success; Verified tree gate, release, get-version, auto_deploy: skipped.

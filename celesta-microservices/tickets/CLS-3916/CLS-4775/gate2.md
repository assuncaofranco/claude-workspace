# CLS-4775 gate 2, rebuilt on master (implementation commit: pending, Lucas commits with the recipe below)

## RECIPE FOR LUCAS (proven, see "Proof")

Plan commit (branch tip, local `CLS-4775` already points at it): `2a7e5328aa`. Base master: `0af9ad3a02`. The merge of `origin/master` into `CLS-4775` is **clean** (no conflicts: the branch only carries the plan file); our change is then copied over it. The pre-commit hook will run phpinsights in your container (mounted on the main clone, so it sees the merged files) over the staged PHP files: it may take a while. If it fails for files that are not ours, send the exact message to the coordinator.

```
git -C /Users/l.franco/Desktop/celesta-projects/celesta-backoffice fetch origin
git -C /Users/l.franco/Desktop/celesta-projects/celesta-backoffice switch CLS-4775
git -C /Users/l.franco/Desktop/celesta-projects/celesta-backoffice merge origin/master --no-commit --no-ff
cp -R /Users/l.franco/Desktop/celesta-projects/claude-workspace/celesta-microservices/tickets/CLS-3916/CLS-4775/final/. /Users/l.franco/Desktop/celesta-projects/celesta-backoffice/
cd /Users/l.franco/Desktop/celesta-projects/celesta-backoffice
git add $(cat /Users/l.franco/Desktop/celesta-projects/claude-workspace/celesta-microservices/tickets/CLS-3916/CLS-4775/FILES.txt)
git status --short | grep -v '^[AMD]  '    # must print nothing
git commit -m "CLS-4775 Merge master into CLS-4775 and resolve the promotion creator in createdBy"
git switch CLS-4758
```

Notes:
- `merge ... --no-commit --no-ff` stages the merge result; it is `merge origin/master` as asked, only without the auto-commit, so the single commit carries merge + change (its message starts with `CLS-4775`, no trailer). A plain `git merge origin/master` would commit with the rejected default message.
- `git add -A` is also safe in a clean clone (ignored files such as `vendor/` and `var/` stay out, proven: same tree), but the explicit list above is the one proven twice. `FILES.txt` lives next to `final/`, not inside it, so `cp -R` does not drop it in the repository root. 14 files, none deleted.
- The `git status` line is a guard: anything it prints is a file that is neither staged nor merged cleanly; stop and tell the coordinator.
- After the commit the coordinator pushes (plain push, no force).

Files copied: `final/` (14 files, repo-relative paths), list in `FILES.txt`:
```
composer.json
composer.lock
src/GatewayBundle/Controller/Promotion/GiftConfigurationController.php
src/GatewayBundle/Controller/Promotion/GiftController.php
src/GatewayBundle/Controller/Promotion/GiftRequestController.php
src/GatewayBundle/Normalizer/Promotion/GiftNormalizer.php
tests/GatewayBundle/Controller/LogControllerTest.php
tests/GatewayBundle/Controller/Promotion/GiftConfigurationControllerTest.php
tests/GatewayBundle/Controller/Promotion/GiftControllerHttpTest.php
tests/GatewayBundle/Controller/Promotion/GiftControllerTest.php
tests/GatewayBundle/Normalizer/Player/LogNormalizerDescriptionTest.php
tests/GatewayBundle/Normalizer/Promotion/GiftNormalizerTest.php
tests/GatewayBundle/Normalizer/Promotion/GiftRequestNormalizerTest.php
tests/Traits/PromotionClientMockTrait.php
```

### Proof

Second throwaway worktree detached at `origin/CLS-4775` (`2a7e5328aa`): `git merge origin/master --no-commit --no-ff` ("Automatic merge went well", 0 unmerged paths), `cp -R final/. .`, `git add -A` -> `git write-tree` = **`ba75421b26b6c3da33feb298bd43a09b4f6944e2`**. Repeated with the explicit `git add $(cat FILES.txt)` instead of `git add -A`: same id `ba75421b26b6c3da33feb298bd43a09b4f6944e2`. Final worktree (master + our change + the plan file `.sdd/_plans/CLS-4775.md`, built with a temporary index seeded from `HEAD`, because master tracks `bin/console` although it is gitignored) -> **`ba75421b26b6c3da33feb298bd43a09b4f6944e2`**. Equal. Merge aborted, scratch worktrees removed. (My first comparison without the plan file and without seeding the index differed in exactly those two paths, `.sdd/_plans/CLS-4775.md` and `bin/console`; both are artefacts of how the comparison tree was built, not of the recipe.)

Prepared message: `CLS-4775 Merge master into CLS-4775 and resolve the promotion creator in createdBy` (no trailer; attribution grep over `final/` prints nothing, see below).

Branch freed: old worktree `/private/tmp/cls3916/celesta-backoffice-4775` removed (its staged work is saved as `staged.patch`, now obsolete), `git branch -f CLS-4775 origin/CLS-4775` done (`2a7e5328aa`), `git worktree list` showed nothing else with it checked out. Lucas's main clone untouched (still `CLS-4758`, clean). The final worktree `/private/tmp/cls3916/celesta-backoffice-4775-final` (detached at `0af9ad3a02`, uncommitted edits) is kept until the coordinator confirms; remove with `git worktree remove --force`.

Will the PR merge cleanly into master after his commit? Yes: the commit is a merge of `origin/master` (`0af9ad3a02`) into the branch, so the PR diff against master is exactly the 15 files below (`.sdd/_plans/CLS-4775.md` + our 14), no conflict as long as master has not moved; if it moves, only the files master touches again can conflict (`composer.lock` is the likely one: master's lock changes with every job-library/fixtures bump).

## 1. Final tree against `origin/master` (`0af9ad3a02`)

`git diff --stat HEAD` in the final worktree (plan file not included, it comes from the branch):

```
 composer.json                                      |   2 +-
 composer.lock                                      |  28 ++--
 .../Promotion/GiftConfigurationController.php      |   2 +-
 .../Controller/Promotion/GiftController.php        |   4 +-
 .../Controller/Promotion/GiftRequestController.php |   2 +-
 .../Normalizer/Promotion/GiftNormalizer.php        |  92 +++++++++++-
 .../GatewayBundle/Controller/LogControllerTest.php |  33 +++++
 .../Promotion/GiftConfigurationControllerTest.php  |  14 ++
 .../Promotion/GiftControllerHttpTest.php           |   1 +
 .../Controller/Promotion/GiftControllerTest.php    |  55 +++++++
 .../Player/LogNormalizerDescriptionTest.php        |  12 ++
 .../Normalizer/Promotion/GiftNormalizerTest.php    | 163 +++++++++++++++++++--
 .../Promotion/GiftRequestNormalizerTest.php        |   5 +-
 tests/Traits/PromotionClientMockTrait.php          |  14 ++
 14 files changed, 393 insertions(+), 34 deletions(-)
```
Attribution grep (`claude|generated with|co-authored|anthropic`) over the 14 files in `final/`: prints nothing.

## 2. Tasks and criteria (paths on the final tree)

| Task | Where | Test |
|---|---|---|
| 1 pin | `composer.json:52` `dev-CLS-4768 as 3.152` (job-library latest tag `v3.151`, checked twice); `composer.lock` job-library -> `dev-CLS-4768` ref `25c8ce84a8b860010d8891eae7b94f68c793237f`; vendor `UserActivityJob` has `SOURCE_TYPE_PROMOTION` (`:24`) and `EVENT_GIFT_REQUESTED` (`:109`), 6 matches for `GIFT_REQUEST` or `SOURCE_TYPE_PROMOTION` | all |
| 2 constructor | `GiftNormalizer.php:25` `PromotionClient` second parameter | `GiftNormalizerTest::setUp`, `GiftRequestNormalizerTest::setUp` |
| 3 domainId | `GiftNormalizer.php:63` `normalizeOne(int $domainId, array $gift)`, `:72` `normalizeMany(int $domainId, array $gifts)` | `GiftNormalizerTest` |
| 4 lookup | `GiftNormalizer.php:258-284` `resolvePromotionConfigurations(): ?array`: `[]` and no call when no id, `getPromotionConfigurations($domainId, filter.ids, limit count, offset 0)`, `V2Exception` -> one error `Gift source promotions could not be fetched` with `source_promotion_ids`, returns `null` | `testNormalizeManyLooksUpTheUsersAndThePromotionsOncePerList`, `testNoPromotionIsLookedUpWhenNoGiftHasASourcePromotion`, `testAFailedPromotionLookupGivesANullCreatedByToPromotionGiftsOnly` |
| 5 normalize | `GiftNormalizer.php:163` third parameter `?array`, `:178` `sourcePromotionId` after `sourceScenarioId` | `testAPromotionGiftResolvesToItsPromotionConfiguration`, `testNormalizeOneDefaultsTheSourcePromotionToNullWhenPromotionDoesNotSendIt` |
| 6 createdBy | `GiftNormalizer.php:176` the `createdBy` entry calls private `normalizeCreatedBy` (`:286-312`): `sourceUserId` set -> master's public `normalizeUser(..., 'sourceUserId', ...)` unchanged (`:228`, not edited); else promotion `{id, name}`; `null` map -> null with no log (`:294`); array without the id -> error `Gift source promotion does not resolve to a promotion configuration` with `gift_id`, `source_promotion_id`, null (`:299-305`) | `testAPromotionMissingFromTheLookupGivesANullCreatedByAndLogsIt`, `testASourceUserWinsOverASourcePromotion` |
| 7 OpenAPI | `GiftNormalizer.php:85` `GiftCreatedBy` description, `:142` `sourcePromotionId` | none (PHP attribute, the plan lists no test) |
| 8 GiftController | `GiftController.php:129` (`postGift`), `:176` (`getGifts`) | `GiftControllerHttpTest::testRecordsAGiftAndReturnsItNormalized` (`'sourcePromotionId' => null`), `GiftControllerTest` |
| 9 GiftConfigurationController | `GiftConfigurationController.php:175` | `GiftConfigurationControllerTest::testListsAPromotionGiftOfAConfigurationWithItsPromotionAsTheCreator` |
| (not in plan) approve | `GiftRequestController.php:231` `normalizeOne($domainId, $gift)`: a caller added on master by CLS-3094; **plan tasks 8 and 9 miss it**, the new signature needs it | `GiftRequestControllerTest` approve cases (44 tests green) |
| 10 mock trait | `PromotionClientMockTrait.php` `'sourcePromotionId' => null` default in `promotionGiftRow`; `mockGetPromotionConfigurationsByIds` next to `mockGetGiftsAggregate` | the HTTP tests |
| 11 tests | below | |

| Acceptance criterion | Test |
|---|---|
| Player list, promotion gift 5 -> `createdBy {5, "VIP tier"}`, `sourcePromotionId` 5 (configuration mocked `disabled`, call carries `filter.ids [5]`, `limit` 1, `offset` 0) | `GiftControllerTest::testListsAPromotionGiftWithItsPromotionAsTheCreator`, `GiftNormalizerTest::testAPromotionGiftResolvesToItsPromotionConfiguration` |
| BO user gift -> user, `sourcePromotionId` null | same HTTP test (second row), `testListsThePlayerGiftsNormalized` (bodies gained `'sourcePromotionId' => null`), `GiftNormalizerTest::testNormalizeManyLooksUpTheUsersAndThePromotionsOncePerList` |
| Scenario gift -> `createdBy` null, `sourceScenarioId` set, `sourcePromotionId` null | `testListsAScenarioGiftWithItsScenarioAndNoCreator`, normalizer many-test row 3 |
| `GET .../gifts` reward configuration list -> same | `GiftConfigurationControllerTest::testListsAPromotionGiftOfAConfigurationWithItsPromotionAsTheCreator` |
| Configuration does not resolve -> null, error with `gift_id`/`source_promotion_id`, 200 | `GiftNormalizerTest::testAPromotionMissingFromTheLookupGivesANullCreatedByAndLogsIt` |
| Lookup error -> null for every promotion gift, one error, none per gift, user gifts keep their user, 200 | `GiftNormalizerTest::testAFailedPromotionLookupGivesANullCreatedByToPromotionGiftsOnly` (two promotion gifts + a user gift, `expects(once())` on `error` with the fetch message), `GiftControllerTest::testListsAPromotionGiftWithNoCreatorWhenPromotionConfigurationsCannotBeFetched` (200) |
| No promotion gift -> no call to `promotion-configurations` | `testNoPromotionIsLookedUpWhenNoGiftHasASourcePromotion` (`never()`), `GiftControllerTest::testDoesNotLookUpPromotionConfigurationsWhenNoGiftComesFromAPromotion` |
| `POST /logs`, `/logs/count` with `sourceTypes ["promotion"]` -> 200, forwarded | `LogControllerTest::testGetLogsFilterActionForwardsThePromotionSourceType`, `::testGetLogsFilterCountActionForwardsThePromotionSourceType` |
| Activity `gift_offered`, source `promotion` -> same description | `LogNormalizerDescriptionTest` data sets `promotion gift offered with a reason` / `without a reason` |
| Both user and promotion -> user wins; row without the key -> null, no lookup | `testASourceUserWinsOverASourcePromotion`, `testNormalizeOneDefaultsTheSourcePromotionToNullWhenPromotionDoesNotSendIt` |

On master's test layout (CLS-4864: `*HttpTest` on the full kernel, `*Test` on `ControllerTestCase`): the new HTTP cases went into the `ControllerTestCase` classes (`GiftControllerTest`, `GiftConfigurationControllerTest`, `LogControllerTest`) like master's own list/offer cases; `GiftControllerHttpTest` only gained the new key in its expected body. Master's cases are untouched. Tests added: `GiftNormalizerTest` +7, `GiftControllerTest` +3, `GiftConfigurationControllerTest` +1, `LogControllerTest` +2, `LogNormalizerDescriptionTest` +2 data sets (suite 4955 -> 4970, +15).

## 3. Commands and real output

Environment: `docker run --rm --network celesta --env-file <compose php environment, `$$`->`$`, from `docker compose config` (read only), in the session scratchpad> -e TEST_TOKEN=4775 -v ~/.composer/auth.json:/root/.composer/auth.json:ro -v <worktree>:/var/www/app -w /var/www/app --entrypoint sh <backoffice:latest-dev image> -c '<cmd>'`. Test DB `backoffice_test4775` (master baseline `backoffice_test7475`, own throwaway worktree, removed). Lucas's `backoffice.php`, `make init` and the compose stack were not touched.

`composer update lancasters/job-library --no-interaction` (final worktree, after `origin/CLS-4768` moved to `25c8ce84a8`):
```
Lock file operations: 0 installs, 1 update, 0 removals
  - Upgrading lancasters/job-library (dev-CLS-4768 8b8f510 => dev-CLS-4768 25c8ce8)
```
then the usual harmless `Failed to copy pre-commit file` (worktree `.git` is a file). Composer rewrote `plugin-api-version` to `2.9.0`, restored to `2.11.0`. Lock diff vs master: job-library entry (`v3.151` -> `dev-CLS-4768`, ref `25c8ce84a8b8`), `aliases`, `stability-flags`, `content-hash`, and composer dropped master's `"published-time"` line of that entry (acceptable, mentioned).

Touched classes, each alone, after the rebuild:
```
tests/GatewayBundle/Normalizer/Promotion (directory)           OK, but there were issues!  Tests: 61, Assertions: 168, Warnings: 1.
tests/GatewayBundle/Controller/Promotion/GiftControllerTest.php             OK (39 tests, 141 assertions)
tests/GatewayBundle/Controller/Promotion/GiftControllerHttpTest.php         OK (5 tests, 15 assertions)
tests/GatewayBundle/Controller/Promotion/GiftConfigurationControllerTest.php OK (29 tests, 90 assertions)
tests/GatewayBundle/Controller/Promotion/GiftRequestControllerTest.php      OK (44 tests, 127 assertions)
tests/GatewayBundle/Controller/LogControllerTest.php                        OK (4 tests, 11 assertions)
tests/GatewayBundle/Controller/LogControllerHttpTest.php                    OK (2 tests, 10 assertions)
tests/GatewayBundle/Normalizer/Player/LogNormalizerDescriptionTest.php      OK (28 tests, 28 assertions)
```
(the 1 warning is the existing `Undefined array key "rewardConfigurationId"` in `normalizeOfferRequest` tests of master.)

Full suite, final tree:
```
FAILURES!
Tests: 4970, Assertions: 12931, Failures: 4, Warnings: 3, Deprecations: 12, PHPUnit Deprecations: 17.
```
Full suite, `origin/master` itself (`0af9ad3a02`):
```
FAILURES!
Tests: 4955, Assertions: 12863, Failures: 4, Warnings: 3, Deprecations: 12, PHPUnit Deprecations: 17.
```
The 4 failures, identical lists (diff of the sorted names prints nothing):
```
Tests\AppBundle\Controller\HealthControllerTest::testProbesIgnoreAnInvalidAuthorizationHeader with data set "readiness" ('/readyz')
Tests\AppBundle\Controller\HealthControllerTest::testReadinessIsServedWithoutAuthentication
Tests\GatewayBundle\Controller\Bonus\BonusControllerHttpTest::testWidestAcceptedRequestStaysWithinMemoryBudget
Tests\GatewayBundle\Controller\Player\TransactionControllerTest::testPostTransactionWithRelatedTransactionId
```
`php scripts/check-route-permissions`: `All route methods have permission checks.`

csfix dry-run over the 12 changed PHP files: `Found 3 of 12 files that can be fixed`; every hunk is on a line that already exists on master (a quote style in `GiftControllerTest.php`, a `.` spacing in the trait, `Generator` imports); the 4 `src` files and my added lines are clean. Write mode not run (it would reformat lines that are not ours).

Lint: `bin/phpinsights analyse <file> --no-interaction --config-path=vendor/lancasters/celesta-dev/config/phpinsights.php` on the 4 changed `src` files: `GiftNormalizer.php` code 97.9, complexity 47.2, architecture 100, style 98.8 (warnings of the kind already there: missing `@param`/`@return` for array parameters, two lines over 120 characters at `:85` and `:143`, the OpenAPI descriptions the plan fixes verbatim); `GiftController.php` 100 / 40 / 100 / 98.8 (two long lines at `:65-66`, master's); `GiftConfigurationController.php` 100 / 46.7 / 100 / 100; `GiftRequestController.php` 100 / 47.6 / 100 / 100. `make coverage` not run (needs the compose container).

## 4. Deviations from the plan

1. Alias `3.152`, not `3.150` (latest job-library tag `v3.151`, re-checked after the library branch moved).
2. A caller the plan does not list: `GiftRequestController::approve` (`:231`, from master's CLS-3094) takes `normalizeOne($domainId, $gift)`; plan tasks 8 and 9 name only `GiftController` and `GiftConfigurationController`. Mechanical, forced by task 3.
3. On master there is no `normalizeCreatedBy` to extend: a private `normalizeCreatedBy` was added that delegates to master's `normalizeUser` for `sourceUserId` and adds the promotion branch (as the amended plan's "On current master" paragraph says); `normalizeUser`, `resolveUsers` and `GiftRequestNormalizer` are unchanged. `GiftRequestNormalizerTest::setUp` builds `GiftNormalizer` with a `PromotionClient` mock (constructor change).
4. New HTTP cases live in master's `ControllerTestCase` classes (layout above); the plan names `GiftControllerTest`, `GiftConfigurationControllerTest`, `LogControllerTest`, so no change in intent.
5. `composer.lock`: `plugin-api-version` restored to `2.11.0`; master's `published-time` line dropped by composer.
6. Test DB `backoffice_test4775`, not the shared one. `FILES.txt` sits beside `final/`, not inside it (it would otherwise be copied into the repository root).
7. No dedicated OpenAPI assertion for `sourcePromotionId`; the plan lists none.
8. Not committed here (hook cannot run from a worktree): `implementation commit: pending`.

## 5. Proteus

None, per the plan.

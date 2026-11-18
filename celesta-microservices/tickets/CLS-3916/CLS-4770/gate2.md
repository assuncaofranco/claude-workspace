# CLS-4770 gate 2

Worktree `/private/tmp/cls3916/celesta-promotion-4770`, branch `CLS-4770`, plan commit `f96901e53`. Not pushed.
The branch is 23 commits behind `origin/master`; worked from this base, master not merged.

## 1. Implementation commit

`605fbd00e2dd2560f170e2f4e3f49f99529b3ad3` `CLS-4770 Add source_promotion_id to gift`

```
git diff --stat f96901e53..HEAD
 features/gift/listing/bo_user_lists_gifts.feature  | 27 ++++++++++++++
 features/gift/offer/bo_user_offers_gift.feature    | 41 ++++++++++++++--------
 features/gift/offer/scenario_offers_gift.feature   | 16 +++++----
 src/ApiBundle/Controller/GiftController.php        |  1 +
 src/AppBundle/Entity/Gift.php                      | 17 +++++++++
 src/Migrations/Version20261117120000.php           | 38 ++++++++++++++++++++
 tests/Builder/Gift.php                             | 14 ++++++--
 .../ApiBundle/Controller/GiftControllerTest.php    | 25 +++++++++++++
 8 files changed, 155 insertions(+), 24 deletions(-)
```

## 2. Tasks and criteria

| Task | Where | Covered by |
|---|---|---|
| 1 migration | `src/Migrations/Version20261117120000.php` (up 18-27, down 29-38) | migrated on dev and test DB; manual down/up, section 3 |
| 2 entity property | `src/AppBundle/Entity/Gift.php:87-90` | all gift Behat features (stored/listed values), openapi check |
| 3 jsonSerialize | `src/AppBundle/Entity/Gift.php:111` | `bo_user_offers_gift.feature:15` (201 + stored), `scenario_offers_gift.feature:13`, `bo_user_lists_gifts.feature:108,126`, early replay in `scenario_offers_gift_once.feature` (unchanged, green) |
| 4 getter/setter | `src/AppBundle/Entity/Gift.php:273-281` | `tests/Builder/Gift.php:40` (setter, via `bo_user_lists_gifts.feature:108`); getter via jsonSerialize |
| 5 late replay | `src/ApiBundle/Controller/GiftController.php:327` | `GiftControllerTest.php:67` (null, key order) and `:100` (stored id) |
| 6 builder | `tests/Builder/Gift.php:22,24,40,109` | `bo_user_lists_gifts.feature:108` (user null, promotion 31) |
| 7 unit test | `tests/Unit/ApiBundle/Controller/GiftControllerTest.php:92` and `:100-123` | itself |
| 8 BO feature | `features/gift/offer/bo_user_offers_gift.feature:34,41` and scenario at `:377` | itself |
| 9 scenario feature | `features/gift/offer/scenario_offers_gift.feature:25,29` | itself |
| 10 listing feature | `features/gift/listing/bo_user_lists_gifts.feature:108` and `:126` | itself |
| 11 run commands | section 3 | |

| Criterion | Where | Covered by |
|---|---|---|
| list returns `sourcePromotionId` (stored id for promotion gift, `null` BO/scenario) | `Gift.php:111` | `bo_user_lists_gifts.feature:108` (31), `:126` (null) |
| gift created before the change: same `sourceUserId`/`sourceScenarioId`, `sourcePromotionId` null | `Gift.php:90` default, column `DEFAULT NULL` | `bo_user_lists_gifts.feature:126`; manual: row 900 kept `source_user_id` 5 across migration down/up, `source_promotion_id` NULL |
| POST 201 with `sourcePromotionId` null; replay 200 equal body through both paths | `Gift.php:111`, `GiftController.php:327` | `bo_user_offers_gift.feature:15`; late: `GiftControllerTest.php:67,100`; early: `scenario_offers_gift_once.feature` (unchanged, green) |
| POST with `sourcePromotionId` -> 400 extra fields, no gift | `GiftType` unchanged | `bo_user_offers_gift.feature:377` |
| OpenAPI `Gift.sourcePromotionId` nullable integer after `sourceScenarioId` | `Gift.php:87-90` | `make openapi`: properties end `..., sourceUserId, sourceScenarioId, sourcePromotionId`; `{'type': ['integer', 'null'], 'example': 31}` |
| column `INT NULL` after migration, gone after `down` | migration | migrate to latest on dev and test DB; `--down` then `--up` executed one SQL each, row intact |

## 3. Test commands and output

Stack: the promotion containers were not running at start (the 4744 mount was gone); `make init` brought them up on
this worktree (`promotion.php` and `promotion.nginx` mounted on `/private/tmp/cls3916/celesta-promotion-4770`).
`make init` first failed on a missing `.env` (git-ignored, absent in a new worktree); copied it from
`/Users/l.franco/Desktop/celesta-projects/celesta-promotion/.env`, re-ran `install.sh --yes`, both DBs migrated to
`Version20261117120000` (71 migrations).

Full output is in this folder: `behat-gift.log`, `phpunit-gift.log`, `behat-rc2.log`, `lint.log`, `openapi.log`.

```
docker compose -f docker-compose.dev.yml exec php bin/console doctrine:database:drop --if-exists --env=test --force
docker compose -f docker-compose.dev.yml exec php bin/console doctrine:database:create --if-not-exists --env=test
docker compose -f docker-compose.dev.yml exec php bin/console doctrine:migrations:migrate --no-interaction --allow-no-migration --env=test
  [notice] finished in 1839.7ms, used 44M memory, 71 migrations executed, 153 sql queries
  [OK] Successfully migrated to version: App\Migrations\Version20261117120000

docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/phpunit tests/Unit/ApiBundle/Controller/GiftControllerTest.php
  OK (8 tests, 26 assertions)

docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/behat features/gift
  113 scenarios (113 passed)
  1128 steps (1128 passed)
  0m7.79s (53.49Mb)

phpunit over every unit test file naming Gift (validators, GiftControllerTest, RewardConfigurationControllerTest,
GiftEventSubscriberTest, GiftFactoryTest)
  OK, but there were issues!
  Tests: 43, Assertions: 137, Deprecations: 1.

behat features/reward_configuration features/reward_offering_reason (they use the gift steps and the builder)
  first run: 249 scenarios (248 passed, 1 failed). Failed:
    features/reward_configuration/offer/bo_user_offers_reward_to_player.feature:11 "Backoffice user successfully offers
    reward configuration to player": result field 'id' mismatch. Expected: 1, Got: 2
  that feature alone: 22 scenarios (22 passed); the two folders again (behat-rc2.log):
  249 scenarios (249 passed)
  1482 steps (1482 passed)
  0m10.07s (53.83Mb)
```

The first-run failure is a bonus `id` of 2 where the scenario expects 1 (auto-increment left by the previous run); it
passed on both reruns and touches no gift code. Not investigated further.

`make lint` (exit 0, checks the three changed src files against `origin/master`): flags only existing code, none on
the lines of this change: `GiftController.php` cyclomatic complexity 11 and 8 and "Single class element per
statement" on the existing consts; `Gift.php:95` `jsonSerialize()` has no `@return` annotation (existing method);
`Version20261117120000.php` clean.

Manual (plan, last paragraph of Testing Strategy):
- `make openapi` exit 0; `components.schemas.Gift.properties` ends `sourceUserId, sourceScenarioId, sourcePromotionId`,
  `sourcePromotionId` = `{'type': ['integer', 'null'], 'example': 31}` (`public/open-api.json` is git-ignored, not committed).
- Dev DB: inserted gift 900 (`source_user_id` 5), `migrations:execute App\Migrations\Version20261117120000 --down`
  (1 sql query), `--up` (1 sql query); after up `SELECT id, source_user_id, source_promotion_id FROM gift` gives
  `900 | 5 | NULL`; row 900 deleted afterwards.

Coverage gates (CI, 100% for both reports) were not run locally; the plan states `Gift.php` and `src/Migrations` are
excluded and the new controller line is reached by both replay tests.

## 4. Deviations from the plan

- Task 1: the migration file was written by hand in the shape of `Version20261019120100`, not generated with
  `doctrine:migrations:generate` (the stack was not mine yet when I wrote it). Timestamp `20261117120000`. Content is
  as the plan says.
- `.env` copied into the worktree from the main clone to make the stack start (ignored by git).
- Task 8 and 10: tables re-aligned where a longer key widened the column (`bo_user_offers_gift.feature`,
  `scenario_offers_gift.feature`): whitespace-only lines in the diff.
- The plan's Testing Strategy has no whole-suite command and `CLAUDE.md` forbids the unfiltered suite; ran the plan's
  commands plus the gift-related unit files and the two Behat folders above, not `make test`.
- `make lint` runs on the committed diff, so the commit was made before it ran (no change was needed after).
- Nothing else beyond the plan.

## 5. Proteus

Worktree `/private/tmp/cls3916/celesta-qaa-proteus-4770`, branch `CLS-4770` from `origin/master` (`de6c7f279`, which
already contains CLS-4540, PR #782). `.env` and `.env.dev` copied from the main clone. Not pushed, not run.

`68bc3b5829863eb0b11f20fe3911b1e571e17d43` `CLS-4770 Add source_promotion_id to the gift data services and the gift suite`

```
git diff --stat origin/master..HEAD
 src/data-services/celesta-promotion/mappers/giftMap.ts           | 1 +
 src/data-services/celesta-promotion/payloads/serviceAPI/gift.ts  | 1 +
 src/data-services/celesta-promotion/payloads/serviceData/gift.ts | 3 ++-
 src/data-services/celesta-promotion/services/serviceData.ts      | 1 +
 src/data-services/types/constants.ts                             | 2 ++
 src/tests/celesta-promotion/service/gift.pcpr-26.test.ts         | 8 ++++--
 6 files changed, 13 insertions(+), 3 deletions(-)
```

What changed: exactly the plan's section (the five data-service links, then the second seeded gift in `beforeAll` with
`source_user_id: null` and `source_promotion_id: faker.number.int(GiftFakeSourcePromotionIdRange)`, precondition text
"offered by a promotion"). No step added or renamed, so no Qase sync.

Checks done without running a suite: `npx eslint` on the changed files (0 errors; 3 existing spellcheck warnings in
`serviceAPI.ts` `optin`, untouched) and `npx tsc --noEmit -p .` (clean), using the main clone's `node_modules` through a
temporary symlink that was removed before the commit.

Not done (rule says to): `qaa-reviewer` agent, `npm run build:unit-test:dev`, the "ask for OAS and SQL before the first
edit" step (no one to ask). Types were decided from the promotion migration and the entity in this branch, not from a
fresh SQL export or OAS; `source_promotion_id` is `INT NULL` there. No `_specs`/`_plans` file exists for PCPR-26's gift
suite in the Proteus repo to update.

Overlap with CLS-4540: it is already merged in Proteus master, so `gift.pcpr-26` already has `giftRequestId` and the
gift request fields, and this commit sits after them (`sourcePromotionId` right after `sourceScenarioId` in the API
type and mapper, `source_promotion_id` after `source_scenario_id` in the DB record). In celesta-promotion `origin/CLS-4540`
has not merged into this branch; the plan's overlap note (entity, replay array, `GiftControllerTest`, `bo_user_lists_gifts.feature`)
still applies to whoever merges second.

## After merging master (2026-11-17)

Why: the first CI run (44110905114) failed in the Proteus Preflight (`Directus field missing: gift.gift_request_id`,
`Directus collection missing: gift_request`): Proteus master already expects CLS-4540's `gift_request`, which was on
promotion `origin/master` and not on this branch (26 commits behind).

Merge commit `f5f289867` `CLS-4770 Merge master into CLS-4770` (merge, no rebase). Review commits before it:
`605fbd00e`, `89c8fde6c`.

Conflicts, three, all the same shape: master added the gift request keys right after `sourceScenarioId`, this branch
added `sourcePromotionId` right after it. Kept both, `sourcePromotionId` first, then master's keys
(`giftRequestId`, `requestedByUserId`, `requestedAt`, `approvedByUserId`, `approvedAt`):
- `src/AppBundle/Entity/Gift.php` `jsonSerialize()`
- `src/ApiBundle/Controller/GiftController.php` late replay array (`resolveIdempotencyKeyRaceWinner`)
- `tests/Unit/ApiBundle/Controller/GiftControllerTest.php` expected array of the replay test
The `.feature` files of gift auto-merged. No line of the CLS-4770 diff changed beyond that placement.

Migration: not renamed. `Version20261117120000` sorts after master's latest (`Version20261116120000`).

Output (stack mounted on this worktree; `install.sh --yes` run after the merge, both DBs at `Version20261117120000`,
73 migrations):
```
GiftControllerTest                                   OK, but there were issues! Tests: 10, Assertions: 33, Deprecations: 6.
phpunit, 9 unit files naming Gift (incl. GiftRequest*) OK, but there were issues! Tests: 66, Assertions: 220, Deprecations: 1.
behat features/gift features/gift_request            172 scenarios (172 passed), 1693 steps (1693 passed)
behat features/reward_configuration + reward_offering_reason
   first run after the DB rebuild: 249 scenarios (248 passed, 1 failed): bo_user_offers_reward_to_player.feature:11,
   "Result field 'id' mismatch. Expected: 1, Got: 2" (same one-off as before, auto-increment);
   rerun: 249 scenarios (249 passed), 1482 steps (1482 passed)
make lint   exit 0; only existing findings: GiftController cyclomatic complexity 9, Gift::jsonSerialize @return
make openapi exit 0; Gift properties end ..., sourceUserId, sourceScenarioId, sourcePromotionId;
   sourcePromotionId = {'type': ['integer', 'null'], 'example': 31}
migration --down: 1 sql query, then `SELECT source_promotion_id FROM gift` -> "1054 Unknown column"; --up: 1 sql query;
   rows after up: (1, source_user_id 1, NULL), (900, source_user_id 5, NULL): existing rows intact, promotion NULL
```

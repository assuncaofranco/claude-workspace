# CLS-4938 — {A} [statistics] Count gifts in the gift KPIs and generosity at completion, not at claim

Sub-task: https://celesta.atlassian.net/browse/CLS-4938 · Parent: https://celesta.atlassian.net/browse/CLS-3865 · Repository: celesta-statistics

## Overview

The Promotion MS sends a `GiftEventJob` when a gift is recorded (`event_type` `created`, `status` `claimed`) and on every later status change (`event_type` `status_changed`). `GiftEventJobHandler` stores each one through `EventBatchProcessor` into `event_promotion`, and the `gift_claimed` KPI in `config/kpi.yaml` aggregates the rows with `event_type: created, status: claimed` into `gift_claimed_amount` / `gift_claimed_count` of `kpi_wallet_sum_daily` and `kpi_wallet_sum`. The `generosity` formula in `kpi_formula` reads `giftClaimedAmount`.

`event_promotion` has `PRIMARY KEY (gift_id)` (`Version20261407000003`), and `EventBatchProcessor::insertBatch()` appends `ON DUPLICATE KEY UPDATE gift_id = gift_id` for idempotent items. So the first event of a gift is the only one ever stored: every `status_changed` event for a gift whose `created` row is still in the table is acked and silently dropped.

[CLS-3865](https://celesta.atlassian.net/browse/CLS-3865) adds the final status `completed` (reached only from `claimed`) and asks that a gift count in the gift KPIs and in generosity only once completed, at the value carried by the `completed` event, in the period of completion; a `claimed` or `canceled` gift counts nowhere. This sub-task changes the key of `event_promotion` so that each status of a gift is stored as its own row, and moves the `gift_claimed` KPI filter from `claimed` to `completed`.

## Architecture & Design

- **Key of `event_promotion`.** The primary key becomes `(gift_id, status)`, mirroring `event_withdraw_request_transaction` (`PRIMARY KEY (withdraw_request_id, status)`, `Version20261406000001`). A gift moves `claimed → completed` or `claimed → canceled` and never returns to a status it had, so each status event is a distinct row, and a redelivered event (same gift, same status) still hits the key and is a no-op. `uniq_promotion_id (id)` and `idx_promotion_date (date)` stay; the auto-increment `id` keeps backing the processing cursor.
- **`EventBatchProcessor` is not changed.** Its `ON DUPLICATE KEY UPDATE <first column> = <first column>` (`gift_id = gift_id`) fires on any unique-key collision, so with the new key it is the redelivery guard for `(gift_id, status)` instead of the guard that dropped every second event.
- **KPI filter.** `gift_claimed` in `config/kpi.yaml` filters `status: completed` only, mirroring `paid_withdrawal` (`status: paid`). With one row per `(gift_id, status)`, a gift has at most one `completed` row, so it counts once. `sum(amount)` reads the amount of that row, which is the gift's value when it was completed, and `date` is the day of its `statusChangedAt`, so the gift lands in the completion period. A `claimed` row and a `canceled` row match nothing.
- **Names are kept.** The KPI key stays `gift_claimed`, the columns stay `gift_claimed_amount` / `gift_claimed_count`, and the API fields stay `giftClaimedAmount` / `giftClaimedCount`. The parent puts renaming the BI fields `gift_claimed_amount` / `gift_claimed_count` out of scope; the `generosity` row in `kpi_formula` reads `giftClaimedAmount`, so keeping the name moves generosity to completed gifts with no formula change; and `kpi_processing_cursor` is keyed by `kpi_name`, so a renamed KPI would start a second cursor from id 0. Only the OpenAPI descriptions of the two fields change, to say what they now count.
- **No change to the producer contract.** `GiftEventJob` (celesta-job-library) already carries `status`, `previousStatus`, `amount` and `statusChangedAt` for `status_changed` events; `GiftEventBatchItem::toRow()` already maps them. The status value `completed` is matched as a literal string in `config/kpi.yaml`, as every other KPI filter is, so this repository does not require the constants library change.
- **Migration.** One non-transactional migration, mirroring `Version20261405000005` (which switched `event_wallet_transaction`'s primary key): `ALTER TABLE event_promotion DROP PRIMARY KEY, ADD PRIMARY KEY (gift_id, status), ALGORITHM=INPLACE, LOCK=NONE`, guarded on the current key being `['gift_id']`. InnoDB runs a primary-key replacement in place with concurrent DML allowed (table rebuild), and `event_promotion` holds at most 14 days of gift events (`kpi:cleanup-events` default retention), so the rebuild is short. Every existing row already has a distinct `gift_id`, so the new key cannot collide on the way up. `down()` first deletes, for each `gift_id`, every row but the one with the lowest `id` (the row the old key would have kept), then restores `PRIMARY KEY (gift_id)` the same way.
- **No recompute.** No KPI row written before the release is touched, and nothing re-reads past events. KPIs change from the first `kpi:process-events` run after the deploy, for event rows past the cursor.

## Implementation Tasks

1. Create `src/Migrations/Version20261408000002.php`, mirroring `Version20261405000005`:
   - `getDescription()`: `Switch event_promotion primary key from gift_id to (gift_id, status) so every status change of a gift is stored`.
   - `isTransactional()` returns `false`.
   - `up()`: return when the table `event_promotion` does not exist; when `$schema->getTable('event_promotion')->getPrimaryKey()?->getColumns() === ['gift_id']`, add `ALTER TABLE event_promotion DROP PRIMARY KEY, ADD PRIMARY KEY (gift_id, status), ALGORITHM=INPLACE, LOCK=NONE`.
   - `down()`: return when the table does not exist; when the primary key columns are `['gift_id', 'status']`, add `DELETE newer FROM event_promotion newer INNER JOIN event_promotion older ON older.gift_id = newer.gift_id AND older.id < newer.id`, then `ALTER TABLE event_promotion DROP PRIMARY KEY, ADD PRIMARY KEY (gift_id), ALGORITHM=INPLACE, LOCK=NONE`.
2. In `src/KPIBundle/Entity/EventPromotion.php`, add `#[ORM\Id]` to the `status` property, so the mapping declares the composite key `(gift_id, status)` as `EventWithdrawRequestTransaction` does. Rewrite the class docblock to say: one row per gift and status (`(gift_id, status)` is the primary key, so a redelivered event for the same gift and status is a no-op via `ON DUPLICATE KEY UPDATE`), while the auto-increment `id` backs the id-based processing cursor; keep the sentence on raw DBAL writes.
3. In `src/KPIBundle/Batch/GiftEventBatchItem.php`, rewrite the docblock of `isIdempotent()` to say that `(gift_id, status)` is the primary key, so a redelivered event for the same gift and status is a no-op via `ON DUPLICATE KEY UPDATE`, and `event_id` is informational. In the class docblock, replace "aggregated into the wallet KPI tables by the gift_claimed KPI" with "aggregated into the wallet KPI tables by the gift_claimed KPI, which counts completed gifts". No code change in the class.
4. In `config/kpi.yaml`, replace the `filter` of `gift_claimed` (`event_type: created`, `status: claimed`) with the single entry `status: completed`. Leave the KPI key, `event_table`, `source` and `fields` unchanged.
5. In `src/KPIBundle/Model/KPIResponse.php`, change the `description` of `giftClaimedAmount` to `Sum of completed physical gifts, at the value carried by the completed event, in the period of completion (Promotion MS gift events, event_promotion)` and of `giftClaimedCount` to `Number of completed physical gifts, in the period of completion`. No other property changes.
6. In `tests/KPIBundle/Kpi/GiftClaimedKpiFlowTest.php`:
   - replace `testClaimedGiftYieldsAmountAndCount` with `testCompletedGiftYieldsAmountAndCount`: a row `event_type` `status_changed`, `status` `completed`, `amount` `30.00` gives `gift_claimed_amount` 30.00 and `gift_claimed_count` 1, and no `__dims`;
   - replace `testStatusChangedGiftEventYieldsNothing` with `testClaimedGiftYieldsNothing`: a row `created` / `claimed` gives `null`;
   - replace `testNonClaimedGiftYieldsNothing` with `testNonCompletedGiftYieldsNothing`: `status_changed` rows with status `canceled` and `claimed`, and a `created` row with status `claimed`, each give `null`;
   - keep `testDefinitionTargetsWalletSourceAndThePromotionEventTable` and `testGiftClaimedDoesNotShareTheWalletEventTable` as they are.
7. In `tests/ApiBundle/Controller/KPIControllerTest.php`, add a private helper `storeGiftEvent(GiftEventJob $job): void` that runs `(new EventBatchProcessor(new NullLogger(), $this->conn()))->process([[new GiftEventBatchItem($job), null]])`, so the test goes through the real insert statement and its `ON DUPLICATE KEY UPDATE`. Add a private helper `giftJob(int $giftId, string $eventType, string $status, ?string $previousStatus, float $amount, string $statusChangedAt): GiftEventJob` that builds a `new GiftEventJob()` with those values, domain 1, player 1, name `Gift <giftId>`, currency `EUR` and `giftCreatedAt` equal to `statusChangedAt` (no KPI reads it).
8. In `KPIControllerTest`, rewrite `testGiftClaimedIsAggregatedFromPromotionGiftEvents` as `testOnlyCompletedGiftsAreAggregatedFromPromotionGiftEvents`, on the same date (yesterday), through `storeGiftEvent`: gift A `created`/`claimed` 30.00 then `status_changed`/`completed` 30.00; gift B `created`/`claimed` 12.50 and nothing else; gift C `created`/`claimed` 99.00 then `status_changed`/`canceled` 99.00. Keep the bonus wallet event and `runWalletProcessEvents()`. After `runGiftProcessEvents()`: `event_promotion` holds 5 rows; the period request returns `giftClaimedAmount` 30.00 and `giftClaimedCount` 1, `bonusClaimedAmount` 50.00 and `bonusClaimedCount` 1; the all-time request returns `giftClaimedAmount` 30.00 and `giftClaimedCount` 1.
9. In `KPIControllerTest`, add `testCompletedGiftCountsOnTheCompletionDayAtTheCompletionValue`: gift `created`/`claimed` 100.00 on D1 (3 days ago), `status_changed`/`completed` 80.50 on D2 (yesterday), then `runGiftProcessEvents()`. The request `from=D1&to=D1` returns `giftClaimedAmount` 0 and `giftClaimedCount` 0; `from=D2&to=D2` returns 80.50 and 1; the all-time request returns 80.50 and 1.
10. In `KPIControllerTest`, add `testGiftEventRedeliveryIsIdempotent`: build one `completed` job (preceded by its `claimed` job) and pass the same `completed` job to `storeGiftEvent` twice. `event_promotion` holds 2 rows; after `runGiftProcessEvents()`, the period request returns `giftClaimedCount` 1 and `giftClaimedAmount` equal to the job amount. Then pass the same `completed` job a third time and run `runGiftProcessEvents()` again: the count stays 1.
11. In `KPIControllerTest`, add `testCompletedEventStoredBeforeItsCreatedEventStillCountsOnce`: store the `status_changed`/`completed` job of a gift before its `created`/`claimed` job. Both rows are stored, and after `runGiftProcessEvents()` the period returns `giftClaimedCount` 1.
12. In `KPIControllerTest`, add `testGenerosityCountsOnlyCompletedGifts`: on yesterday, `insertPaymentDaily($date, 100.00, 1)`; gift A `created`/`claimed` 30.00 then `status_changed`/`completed` 20.00; gift B `created`/`claimed` 40.00 only; `runGiftProcessEvents()`. The request with both wallet and payment returns `giftClaimedAmount` 20.00 and `generosity` 20.00 (20 / 100 × 100; no bonus).
13. Leave `testGetKpiActionGenerosityIncludesClaimedGifts`, `tests/KPIBundle/Batch/GiftEventBatchItemTest.php` and `tests/KPIBundle/MessageHandler/GiftEventJobHandlerTest.php` unchanged: they seed aggregate rows or mock the processor, and the row mapping does not change.
14. Run `make openapi` so `public/open-api.json` (not versioned) carries the new descriptions and lints clean.

## File Changes

**Create**
- `src/Migrations/Version20261408000002.php` — `event_promotion` primary key `(gift_id)` → `(gift_id, status)`, with a `down()` that restores the old key (task 1)

**Modify**
- `src/KPIBundle/Entity/EventPromotion.php` — `#[ORM\Id]` on `status`, docblock (task 2)
- `src/KPIBundle/Batch/GiftEventBatchItem.php` — docblocks only (task 3)
- `config/kpi.yaml` — `gift_claimed` filter `status: completed` (task 4)
- `src/KPIBundle/Model/KPIResponse.php` — descriptions of `giftClaimedAmount` and `giftClaimedCount` (task 5)
- `tests/KPIBundle/Kpi/GiftClaimedKpiFlowTest.php` — completed counts, claimed and canceled do not (task 6)
- `tests/ApiBundle/Controller/KPIControllerTest.php` — helpers and five gift tests through the real batch insert (tasks 7–12)

**Read, not modified**
- `src/KPIBundle/Batch/EventBatchProcessor.php` — the `ON DUPLICATE KEY UPDATE` built from the first column, which becomes the redelivery guard for the new key
- `src/Migrations/Version20261405000005.php` — the primary-key switch pattern to mirror
- `src/KPIBundle/Entity/EventWithdrawRequestTransaction.php`, `src/Migrations/Version20261406000001.php` — the `(id, status)` key pattern
- `src/Migrations/Version20261407000002.php` — the `generosity` formula reading `giftClaimedAmount`
- `src/KPIBundle/Kpi/Processing/KpiReconsolidateProcessor.php`, `src/KPIBundle/Command/KpiEventsCleanupCommand.php` — unchanged; see Edge Cases

## Testing Strategy

Inside the container (`make exec`):

- `bin/phpunit tests/KPIBundle/Kpi/GiftClaimedKpiFlowTest.php` — the `gift_claimed` definition counts a `completed` row and nothing for `claimed` or `canceled`.
- `bin/phpunit tests/ApiBundle/Controller/KPIControllerTest.php --filter Gift` — through the real batch insert and `kpi:process-events promotion`: claim then complete stores two rows and counts once; claimed-only and canceled count nowhere; the completion day and completion value are used; a redelivered `completed` event stores no second row and counts once; a `completed` event stored before its `created` event counts once; generosity includes only the completed amount.
- `make test` — recreates the test database through `doctrine:migrations:migrate`, so the new migration's `up()` runs before the suite; full results in `var/log/phpunit.log`. Coverage excludes `src/Migrations` and `src/*Bundle/Entity`.
- `make lint` and `make openapi`.

Manual verification, on the dev database:

- `bin/console doctrine:migrations:migrate --no-interaction`, then `SHOW KEYS FROM event_promotion WHERE Key_name = 'PRIMARY'` lists `gift_id`, `status`.
- `bin/console doctrine:schema:validate --skip-sync` reports the mapping valid, and `bin/console doctrine:schema:update --dump-sql` shows no change for `event_promotion` (entity and migration agree).
- With two rows for one gift (`claimed`, `completed`), `bin/console doctrine:migrations:execute 'App\Migrations\Version20261408000002' --down` leaves only the `claimed` row and the key `(gift_id)`; `--up` again restores `(gift_id, status)`.

## Proteus tests

None to add or update. The criteria of this sub-task are about which gift events become KPI values, through the SQS consumer and the `kpi:process-events` cron; celesta-qaa-proteus seeds the aggregate tables directly for the statistics service suite (`src/tests/celesta-statistics/service/KPI/kpi.pcst-3.test.ts`) and cannot drive the event pipeline. The response contract does not change (same fields, same types; only the OpenAPI descriptions), so that suite stays as it is. The criteria are covered by the database-backed tests in `KPIControllerTest` above.

## Edge Cases & Error Handling

- **Redelivered event.** Same gift, same status: the insert hits `(gift_id, status)` and `ON DUPLICATE KEY UPDATE gift_id = gift_id` makes it a no-op; the KPI does not change.
- **Events out of order.** SQS does not order messages. A `completed` row stored before its `claimed` row is still one `completed` row, dated on its own `statusChangedAt`, and counts once.
- **Value edits.** The Promotion MS sends no event for a value edit (only for a status change), so nothing is stored; the `completed` event carries the final value, and that is the amount summed.
- **Completion on another day than the claim.** `date` is the day of the event's `statusChangedAt`, so the gift counts on the completion day and not on the claim day.
- **Currencies.** Aggregated per currency without conversion, unchanged.
- **Gifts recorded before the release.** No special rule. A claimed gift whose `created` row was processed before the deploy has already been counted at claim and counts again when completed; a `created` row stored before the deploy but processed after it is no longer counted. No gift has been recorded in production yet, so neither case changes a reported figure.
- **`kpi:reconsolidate` for `wallet`.** It rebuilds daily rows from the retained `event_promotion` rows with the new filter. Run over a period that still holds pre-release `claimed` rows, it drops them from that period. Same rule as above: no special handling.
- **14-day retention.** `kpi:cleanup-events` deletes event rows older than 14 days that are behind the cursor. A `claimed` row may be deleted before the gift is completed; the `completed` row then inserts without conflict and counts. A `completed` event redelivered after its row was deleted would be stored and counted again; SQS keeps a message at most 14 days, so a redelivery cannot come later than the retention.
- **Deploy window.** The Promotion MS starts sending `completed` events only with [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941). If it ships before this sub-task, the current key drops every `completed` event and the message is acked, so it is not replayed: those gifts never count. This sub-task deploys first. Between the two deploys, new gifts are `claimed` only and count nowhere.
- **Migration.** `ALGORITHM=INPLACE, LOCK=NONE` keeps inserts flowing during the rebuild. If the server refuses the in-place algorithm, the statement fails instead of falling back to a locking copy; the migration is not marked as executed and can be rerun.
- **Rollback.** `down()` keeps one row per gift (the lowest `id`) and restores `PRIMARY KEY (gift_id)`. KPI rows already written are not touched. If the consumer inserts a second row for a gift between the `DELETE` and the `ALTER`, the `ALTER` fails on the duplicate; rerunning `down()` deletes it and succeeds. After a rollback the previous code counts at claim again and drops `completed` events, so the Promotion MS change ([CLS-4941](https://celesta.atlassian.net/browse/CLS-4941)) is rolled back first.

## Acceptance criteria

- A gift's `created` event (`claimed`) and its `status_changed` event (`completed` or `canceled`) are both stored in `event_promotion`, one row each.
- A redelivered event for the same gift and status stores no second row and changes no KPI value.
- A completed gift counts once in `giftClaimedCount`, and its completion value in `giftClaimedAmount`, in the daily KPI of its completion date and in the all-time KPI.
- A gift claimed for 100.00 and completed at 80.50 adds 80.50, not 100.00.
- A gift claimed on D1 and completed on D2 counts on D2 and not on D1.
- A gift that is only claimed counts nowhere; a canceled gift counts nowhere.
- `generosity` includes the amount of completed gifts only, with no change to its formula.
- `GET /api/kpi/{playerId}` keeps the fields `giftClaimedAmount` and `giftClaimedCount` with the same types.
- No KPI row written before the release is recomputed or changed by the deploy.

## Dependencies

- Parent: [CLS-3865](https://celesta.atlassian.net/browse/CLS-3865).
- Blocks [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941) — the Promotion MS Complete action. Deploy order: this sub-task (migration and filter) goes to production before CLS-4941, because the current key drops `completed` events for good.
- Related to [CLS-4935](https://celesta.atlassian.net/browse/CLS-4935) — the `completed` status value. This repository matches it as a literal string in `config/kpi.yaml` and does not require the constants library.
- Related to [CLS-4939](https://celesta.atlassian.net/browse/CLS-4939) — the same rule for the BI `player_kpi` tables, in celesta-terraform-bi.
- Related to [CLS-4435](https://celesta.atlassian.net/browse/CLS-4435) — replaced by this sub-task.
- The migration is named `Version20261408000002`: newer than the latest on master (`Version20261407000004`) and than `Version20261408000001`, which the open `CLS-4754` branch adds.
- No Team O or Team QAA service-desk request.

## Out of Scope

- Renaming `gift_claimed_amount` / `gift_claimed_count`, the `gift_claimed` KPI or the API fields (the parent excludes the BI rename, and the formula reads the current name).
- Recomputing KPI periods before the release, or migrating gift events recorded before it.
- Sending the `completed` event and the final value from the Promotion MS ([CLS-4941](https://celesta.atlassian.net/browse/CLS-4941)).

## Decisions

- **How are gifts recorded before the release counted?** — No special rule: a gift already counted at claim may count again when completed, and a claimed event processed after the deploy is not counted. No gift has been recorded in production, and counting one twice is acceptable. The parent's criterion "Gift recorded before release" is to be dropped on the parent; pending product owner confirmation · answered by Lucas Franco, 2026-11-17
- **Statistics stores only the first event of a gift (`PRIMARY KEY (gift_id)` with `ON DUPLICATE KEY UPDATE gift_id = gift_id`); how is the `completed` event kept?** — This sub-task changes the key of `event_promotion` so that each status of a gift is its own row, because the KPI must read the `completed` event · answered by Lucas Franco, 2026-11-17
- **Which goes first, this change or the Promotion MS Complete action?** — Statistics deploys before the Complete action of the Promotion MS, because a `completed` event dropped by the current key is acked and never replayed · answered by Lucas Franco, 2026-11-17

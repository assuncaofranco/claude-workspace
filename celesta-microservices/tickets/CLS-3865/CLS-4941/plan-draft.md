# CLS-4941: Complete a claimed gift and edit its value

Sub-task [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941) · parent [CLS-3865](https://celesta.atlassian.net/browse/CLS-3865) (Story: Edit gift value and complete gifts to order) · repository `celesta-promotion`

## Overview

After [CLS-4434](https://celesta.atlassian.net/browse/CLS-4434) a gift is `claimed` or `canceled`, and `PATCH /api/domain/{domainId}/player/{playerId}/gift/{giftId}` moves a `claimed` gift to `canceled` under a row lock. This sub-task adds the two backoffice actions of the parent on the same operation:

- **Complete**: `{"status": "completed"}` moves a `claimed` gift to the final status `completed`. The status and its transition come from celesta-constants ([CLS-4935](https://celesta.atlassian.net/browse/CLS-4935)); the existing workflow and the existing `status_changed` statistics event do the rest.
- **Edit value**: `{"amount": "80.50"}` changes the amount of a `claimed` gift, with the offer's value rules, the currency unchanged, and the previous amount in the response so the backoffice can write the `gift_value_edited` activity event.

Both run inside the transaction and row lock of `GiftService`, so two actions on one gift are applied one after the other.

## Acceptance criteria

Complete:

- `PATCH …/gift/{giftId}` with `{"status":"completed"}` on a `claimed` gift returns 200 with the gift, `status` `completed`, and stores it.
- The same request on a `completed` gift returns 400 with `Impossible to change status from completed to completed.` and changes nothing.
- The same request on a `canceled` gift returns 400 and the gift stays `canceled`.
- `{"status":"canceled"}` on a `completed` gift returns 400 and the gift stays `completed`.
- Each successful complete queues exactly one `GiftEventJob` with `eventType` `status_changed`, `status` `completed`, `previousStatus` `claimed`, and the gift's amount at completion (the edited amount when it was edited before); a rejected complete queues none.

Edit value:

- `{"amount":"80.50"}` on a `claimed` gift of 100.00 EUR returns 200 with the gift, `amount` `"80.50"`, `currency` `"EUR"`, `previousAmount` `"100.00"`, and stores `80.50`.
- The amount is stored and returned with two decimals: `"80.5"` and the JSON number `80.5` both give `"80.50"`.
- `0.01` and `99999999.99` are accepted; `0`, a negative value, three decimals, nine integer digits, a non-numeric value, an empty string, `null` each return 400 and store nothing.
- An edit on a `completed` or a `canceled` gift returns 400 with an error on `amount` and leaves the amount unchanged.
- A body with `currency`, `status` or any field other than `amount` next to `amount` returns 400 and changes nothing.
- An edit to the gift's current amount (`"100"` or `"100.00"` on a gift of 100.00) returns 200 with `previousAmount` equal to `amount` and stores nothing.
- An edit queues no `GiftEventJob`.

Both:

- A `claimed` gift whose reward configuration is disabled, soft-deleted, or absent (gifts recorded before CLS-4034) can be edited and completed.
- An unknown gift, or one of another player or another domain, returns 404 for both actions.
- Two actions on one gift are applied one after the other: complete × complete gives one 200 and one 400; complete then edit gives 200 then 400; edit then complete gives 200 and 200, and the `completed` event carries the edited amount; edit × edit gives two 200s, each response carries the amount that request sent and the amount before it, and the last one is stored.
- The generated OpenAPI documents both request bodies and both responses of `gift_update`, and the gift `status` enum lists `completed`.

## Architecture & Design

**Base.** The branch merges `origin/CLS-4434` (PR #592, approved, not on master) before any change, because every class below is the one CLS-4434 creates or changes. The plan's pull request targets master; until #592 merges, its diff also shows #592's changes.

**Constants.** `Lancaster\Constants\Promotion\GiftConstants` gains, in celesta-constants on branch `CLS-4935` (from that repository's `CLS-4434`): `STATUS_COMPLETED = 'completed'`, appended to `STATUSES`, and a transition named `completed` in `STATUS_TRANSITIONS`, from `[claimed]` to `completed`. Nothing is added to `canceled`'s `from`, so `completed` is final. This repository pins that branch instead of `dev-CLS-4434`; no constant is created here.

**Complete.** No new code path. `gift_status_workflow` (`config/packages/framework.yaml`) reads its places and transitions from `GiftConstants`, `GiftStatusType` accepts any string, and the `#[Workflow]` constraint on `Gift` decides. With the new pin, `{"status":"completed"}` from `claimed` passes; from `completed` or `canceled` the constraint returns `Impossible to change status from <old> to completed.`; `canceled` from `completed` fails the same way. `GiftEventSubscriber` already emits `status_changed` with `previousStatus` from the change set and the amount on the entity at flush. Only the OpenAPI of `GiftStatusType` changes: `enum` `[canceled, completed]`, description "`canceled` or `completed`, from `claimed` only."

**Edit value — contract.** Same operation, `PATCH /api/domain/{domainId}/player/{playerId}/gift/{giftId}`, `gift_update`. The body is one of:

```json
{ "status": "completed" }
```

```json
{ "amount": "80.50" }
```

A body with an `amount` key is an edit; any other body is a status change, exactly as CLS-4434 handles it (so `{}` keeps its 400). Response of an edit, 200:

```json
{ "id": 1, "status": "claimed", "amount": "80.50", "currency": "EUR", "…": "every other Gift field", "previousAmount": "100.00" }
```

400 is the standard `validation-errors` body: the field errors from the value rules, `This form should not contain extra fields.` for any field next to `amount` (`currency`, `status`, `name`, …), and `The amount of a <status> gift cannot be edited.` on `amount` for a gift that is not `claimed`. 404 as for the status change.

**Edit value — why a separate form on a request model.** The `#[Workflow]` constraint on `Gift` runs whenever a form bound to the `Gift` entity is validated, and refuses an unchanged status (`Impossible to change status from claimed to claimed.`). An edit therefore validates a request model, `App\ApiBundle\Model\Request\GiftAmount`, through `App\ApiBundle\Form\Type\Gift\GiftAmountType`, and the service copies the amount onto the gift only after validation. The form has the single field `amount`, so `currency` or `status` next to it is an extra field and the form's default `allow_extra_fields: false` refuses it.

**Value rules.** The offer's rules on `App\ApiBundle\Model\Request\Gift::$amount` (`Type('numeric')`, `GreaterThan(0)`, `Regex('/^\d{1,8}(\.\d{1,2})?$/')` with "This value should have at most two decimals.") move into one compound constraint, `App\ApiBundle\Validator\Constraints\Gift\GiftAmountConstraint` (extends `Symfony\Component\Validator\Constraints\Compound`), used by both models, so the offer and the edit cannot drift. `GiftAmount::$amount` adds `NotBlank`, because an edit must carry a value; the offer's amount stays optional.

**Service.** `GiftService` keeps the transaction and the lock in one public method and branches inside them:

- `update(int $domainId, int $playerId, int $giftId, array $payload): Gift|GiftAmountEdit|FormInterface|null` replaces the public `changeStatus`. Inside `$this->em->getConnection()->transactional(...)`: `findPlayerGiftForUpdate` (null → null); `\array_key_exists(GiftAmountType::FIELD_AMOUNT, $payload)` → `editAmount`, otherwise → `changeStatus`.
- `changeStatus(Gift $gift, array $payload): Gift|FormInterface`, private: the CLS-4434 body after the lookup, unchanged.
- `editAmount(Gift $gift, array $payload): GiftAmountEdit|FormInterface`, private:
  1. create `GiftAmountType` on a new `GiftAmount`, `method` PATCH, `submit($payload)`; invalid → return the form;
  2. the gift is not `GiftConstants::STATUS_CLAIMED` → add `new FormError(sprintf(self::AMOUNT_NOT_EDITABLE_MESSAGE, $gift->getStatus()))` to the `amount` field and return the form, as `GiftController::postGift` does for the out-of-stock error;
  3. `$previousAmount = $gift->getAmount()`; `$amount = bcadd($model->getAmount(), '0', GiftFactory::AMOUNT_SCALE)`;
  4. `bccomp($previousAmount, $amount, GiftFactory::AMOUNT_SCALE) !== 0` → `$gift->setAmount($amount)` and `$this->em->flush()`; equal → nothing is written;
  5. return `new GiftAmountEdit($gift, $previousAmount)`.

The status is checked on the locked row, so an edit that waited behind a complete sees `completed` and is refused. An amount-only flush has no `status` in its change set, so `GiftEventSubscriber` emits nothing; `updatedAt` moves, as on any write.

**Response model.** `App\AppBundle\Model\GiftAmountEdit`, `final readonly`, constructor `(Gift $gift, string $previousAmount)`, implements `JsonSerializable`: `$this->gift->jsonSerialize() + ['previousAmount' => $this->previousAmount]`. Its `#[OA\Schema]` is `allOf` the `Gift` schema and a `previousAmount` string property (example `"100.00"`, description "Amount before this edit; equal to `amount` when nothing changed.").

**Controller.** `GiftController::patchGift` calls `update` instead of `changeStatus`; the mapping stays (null → 404, form → returned, otherwise `new JsonResponse($result)`). OpenAPI: summary "Cancel or complete a gift, or edit its amount"; `#[OA\RequestBody]` `oneOf` `GiftStatusType` and `GiftAmountType`; `#[COA\SuccessfulResponse]` `oneOf` `Gift` and `GiftAmountEdit`; the 400, 403, 404 and 500 refs unchanged.

**Concurrency.** The row lock of `findPlayerGiftForUpdate` serializes every action on one gift; there is no version column. A transition after any action is checked by the workflow against the committed status; an edit after a transition is refused by the status check; two edits both pass, in order, each answered with its own amount and the amount it replaced.

**No migration.** `gift.amount` (`DECIMAL(10,2)`) and `gift.status` (`VARCHAR(32)`) already hold both changes.

**Who can call it.** Unchanged from CLS-4434: only the backoffice proxy, behind the guard secret. Permissions and the activity events (`gift_value_edited`, `gift_completed`) are the backoffice's.

## Implementation Tasks

1. While #592 is not on master, merge `origin/CLS-4434` into `CLS-4941` with the commit `CLS-4941 Merge branch 'CLS-4434' into CLS-4941`. If #592 is on master by then, skip this task.
2. In `composer.json`, change `lancasters/constants` from `dev-CLS-4434 as 1.367` to `dev-CLS-4935 as 1.371`, then run `composer update lancasters/constants` in the container so `composer.lock` follows. Before writing it, check the latest celesta-constants tag: 1.371 is the next version after tag v1.369 and the 1.370 that `dev-CLS-4767` already uses; if either moved, take the next free one.
3. In `src/ApiBundle/Form/Type/Gift/GiftStatusType.php`, change the `status` property of `#[OA\Schema]` to `enum: [GiftConstants::STATUS_CANCELED, GiftConstants::STATUS_COMPLETED]` and the description to "`canceled` or `completed`, from `claimed` only."
4. In `src/AppBundle/Factory/GiftFactory.php`, make `AMOUNT_SCALE` public.
5. Create `src/ApiBundle/Validator/Constraints/Gift/GiftAmountConstraint.php`, a `Compound` constraint usable as a property attribute, whose `getConstraints()` returns the three amount constraints of `Model/Request/Gift.php` with their current message.
6. In `src/ApiBundle/Model/Request/Gift.php`, replace the three amount attributes with `#[GiftAmountConstraint]`.
7. Create `src/ApiBundle/Model/Request/GiftAmount.php`: `private ?string $amount = null` with `#[Assert\NotBlank]` and `#[GiftAmountConstraint]`, `getAmount(): ?string`, and `setAmount(int|float|string|null $amount): self` casting like `Model/Request/Gift::setAmount`.
8. Create `src/ApiBundle/Form/Type/Gift/GiftAmountType.php`, mirroring `GiftStatusType`: `public const string FIELD_AMOUNT = 'amount'`; one `amount` `TextType` field; `data_class` `GiftAmount`; `#[OA\Schema(required: ['amount'])]` with `amount` a string, example `"80.50"`, description "Greater than 0, at most 8 integer digits and 2 decimals. Only a claimed gift; no other field may be sent."
9. Create `src/AppBundle/Model/GiftAmountEdit.php` as under Architecture & Design.
10. In `src/AppBundle/Service/GiftService.php`, add `public update(...)`, make `changeStatus` private and take the locked gift, add private `editAmount`, all as under Architecture & Design; the message is `private const string AMOUNT_NOT_EDITABLE_MESSAGE = 'The amount of a %s gift cannot be edited.'`.
11. In `src/ApiBundle/Controller/GiftController.php`, call `$this->giftService->update(...)` in `patchGift` and change its OpenAPI attributes as under Architecture & Design.
12. In `tests/Unit/ApiBundle/Controller/GiftControllerTest.php`, add the cases under Testing Strategy.
13. In `tests/Acceptance/Steps/GiftSteps.php`, add the steps under Testing Strategy.
14. In `features/gift/cancel/bo_user_cancels_gift.feature`, replace the `completed` example of "A status other than canceled is refused" with `offered` / `Impossible to change status from claimed to offered.`: `completed` is now a valid transition from `claimed`.
15. Create `features/gift/complete/bo_user_completes_gift.feature` and `features/gift/edit/bo_user_edits_gift_amount.feature` with the scenarios under Testing Strategy.
16. Run `make openapi` and check in `public/open-api.json` (gitignored, not committed) that `gift_update` has both bodies and both responses and the gift `status` enum lists `completed`.

## File Changes

**Create**

- `src/ApiBundle/Validator/Constraints/Gift/GiftAmountConstraint.php` — the gift amount rules, shared by offer and edit
- `src/ApiBundle/Model/Request/GiftAmount.php` — edit request model
- `src/ApiBundle/Form/Type/Gift/GiftAmountType.php` — edit body, `amount` only
- `src/AppBundle/Model/GiftAmountEdit.php` — edit response, the gift plus `previousAmount`
- `features/gift/complete/bo_user_completes_gift.feature`
- `features/gift/edit/bo_user_edits_gift_amount.feature`

**Modify**

- `composer.json`, `composer.lock` — `lancasters/constants` on `dev-CLS-4935`
- `src/ApiBundle/Form/Type/Gift/GiftStatusType.php` — OpenAPI enum and description
- `src/ApiBundle/Model/Request/Gift.php` — amount rules through `GiftAmountConstraint`
- `src/AppBundle/Factory/GiftFactory.php` — `AMOUNT_SCALE` public
- `src/AppBundle/Service/GiftService.php` — `update`, private `changeStatus` and `editAmount`
- `src/ApiBundle/Controller/GiftController.php` — `patchGift` calls `update`; OpenAPI
- `tests/Unit/ApiBundle/Controller/GiftControllerTest.php` — complete and edit cases
- `tests/Acceptance/Steps/GiftSteps.php` — edit and free-body steps
- `features/gift/cancel/bo_user_cancels_gift.feature` — `completed` example replaced by `offered`

Plus the files of the `origin/CLS-4434` merge (task 1).

## Testing Strategy

**Behat steps,** in `GiftSteps`, sent through the existing private `changeGiftStatus($giftId, $playerId, $payload)`:

- `When the BO user edits the amount of the gift to :amount` — body `{"amount": <amount>}` on the current gift
- `When the BO user edits the amount of gift :giftId of player :playerId to :amount`
- `When the BO user sends a change for the gift with:` — body from the table through the existing `tableToPayload`, so values are JSON (`"80.50"`, `80.5`, `null`)

Existing steps reused: `a gift exists with:` (with `status` and `amount`), `a gift reward configuration :name exists in domain :domainId with status :status`, `the gift reward configuration :name was deleted`, `the gift is linked to the gift reward configuration :name`, `the statistics KPI queue is empty`, `a status changed gift KPI event should be queued from :previousStatus`, `the gift KPI event amount should be :amount`, `no status changed gift KPI event should be queued`, `the gift should be stored with:`, `result should have data`.

**`features/gift/complete/bo_user_completes_gift.feature`.** Background: BO user of domain 1 logged in, a gift reward configuration "Hamper gift" in EUR.

- Complete a `claimed` gift linked to its configuration: 200, `status` `completed` in the response and in storage; one status changed KPI event from `claimed`, amount `10.00`.
- Complete a gift whose configuration is disabled; whose configuration was deleted; with no configuration: each 200, stored `completed`, one event.
- Complete a gift twice: the second is a validation error `Impossible to change status from completed to completed.`, no status changed KPI event after the first.
- Complete a `canceled` gift: validation error `Impossible to change status from canceled to completed.`, stored `canceled`, no event.
- Cancel a `completed` gift: validation error `Impossible to change status from completed to canceled.`, stored `completed`, no event.
- Edit the amount to `80.50`, then complete: the complete is 200 and its KPI event amount is `80.50`.
- Complete a gift of another player: not found, stored `claimed`, no event.
- Listing gifts with filter `statuses` `completed` returns the completed gift only.

**`features/gift/edit/bo_user_edits_gift_amount.feature`.** Same background, gift of `100.00` EUR.

- Edit to `80.50`: 200, `amount` `"80.50"`, `currency` `"EUR"`, `previousAmount` `"100.00"`; stored `80.50`; no status changed KPI event.
- Scenario outline on accepted values: `"80.5"` → `"80.50"`; JSON number `80.5` → `"80.50"`; `"0.01"`; `"99999999.99"`.
- Scenario outline on refused values, each a validation error, stored `100.00`: `"0"`, `"-5"`, `"10.123"`, `"123456789"`, `"abc"`, `""`, `null`.
- Edit to `"100"` and to `"100.00"`: 200, `amount` and `previousAmount` both `"100.00"`.
- Edit with `currency` `"USD"` next to `amount`; with `status` `"completed"` next to `amount`: each a validation error `This form should not contain extra fields.`, stored `100.00` EUR `claimed`.
- Edit a `completed` gift; a `canceled` gift: validation error `The amount of a completed gift cannot be edited.` / `… canceled …`, amount unchanged.
- Edit a gift whose configuration is disabled; deleted; absent: each 200, stored `80.50`.
- Edit twice, `80.50` then `70.00`: both 200; the second has `previousAmount` `"80.50"`; stored `70.00`.
- Complete, then edit: the edit is a validation error, amount unchanged.
- Edit gift 999 of player 42: not found.

**PHPUnit,** `GiftControllerTest`, so every branch of `GiftService` and `GiftAmountEdit` is in the PHPUnit-only coverage report (`phpunit.xml` measures `src/AppBundle`, not `src/ApiBundle`):

- completes a claimed gift (200, `status` `completed`);
- edits the amount of a claimed gift (200, `amount` `"80.50"`, `previousAmount` `"10.00"`);
- refuses an invalid amount (400);
- refuses an amount edit on a completed gift (400);
- answers an edit to the current amount with `previousAmount` equal to `amount` (200);
- the existing cancel, refused status change and not found cases stay.

Commands, inside the container, with `XDEBUG_MODE=off`:

- `docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/phpunit tests/Unit/ApiBundle/Controller/GiftControllerTest.php tests/Unit/AppBundle/EventListener/Job/GiftEventSubscriberTest.php tests/Unit/AppBundle/Factory/GiftFactoryTest.php`
- `docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/behat features/gift`

Manual: from two shells at the same moment, send complete and complete, then complete and edit, on one claimed gift. Each pair gives one 200 and one 400, and the row holds the first change.

## Proteus tests

In celesta-qaa-proteus, suite `src/tests/celesta-promotion/service/gift.pcpr-26.test.ts`, a new block "Completing and re-valuing gifts", on a gift the suite offers in its setup. `GiftStatus` gains `completed`; the edit response type is `GiftApiResponse` plus `previousAmount: string` in `payloads/serviceAPI/gift.ts`.

| Request | Expected | Parent criterion |
|---|---|---|
| `PATCH /api/domain/{domainId}/player/{playerId}/gift/{giftId}` `{"amount":"80.50"}` on a claimed gift of 100.00 | 200, `amount` `"80.50"`, `currency` unchanged, `previousAmount` `"100.00"`; matches the OpenAPI | Edit value requires a value greater than 0 with at most 2 decimals; currency is read-only |
| same, `{"amount":"80.50"}` again | 200, `previousAmount` = `amount` = `"80.50"` | (edit to the same value) |
| same, `{"amount":"10.123"}` | 400 validation error, amount unchanged | an invalid value saves nothing |
| same, `{"amount":"70.00","currency":"USD"}` | 400, currency and amount unchanged | currency is read-only |
| same, `{"status":"completed"}` | 200, `status` `completed`, `amount` `"80.50"`; matches the OpenAPI | Complete sets `completed` |
| same, `{"status":"completed"}` again | 400 | the API rejects any transition on a completed gift |
| same, `{"amount":"70.00"}` | 400, amount `"80.50"` | the API rejects a value edit on a completed gift |
| same, `{"status":"canceled"}` | 400, `status` `completed` | the API rejects any transition on a completed gift |
| `GET /api/domain/{domainId}/gifts?filter[statuses][]=completed&filter[ids][]={giftId}` | one gift, `status` `completed` | a completed gift leaves To order and shows in Ordered |

Not observable by the suite, covered here instead: the statistics message on complete and none on edit (Behat, KPI transport); two simultaneous actions (Behat in sequence, manual in parallel); disabled and deleted configurations (Behat).

## Edge Cases & Error Handling

- **Gift not `claimed`:** complete or cancel → 400 from the workflow constraint; edit → 400 on `amount` from the status check; nothing flushed, no event.
- **Two actions at once:** serialized by the row lock; the second reads the committed row. Two edits both succeed in order.
- **Same amount:** 200, nothing written, `updatedAt` unchanged, `previousAmount` = `amount`.
- **Amount format:** stored and answered with two decimals (`bcadd` to `GiftFactory::AMOUNT_SCALE`); comparison with `bccomp` at the same scale, so `"100"` equals `"100.00"`.
- **`amount` with any other field:** 400 extra fields; `{}` or a body without `amount` keeps the CLS-4434 status behaviour.
- **Disabled, soft-deleted or absent configuration:** neither action loads the configuration; `jsonSerialize` reads only its id.
- **Unknown gift, other player, other domain:** 404; the lookup locks nothing it does not return.
- **Lock wait timeout:** DBAL throws, the transaction rolls back, 500, nothing changed.
- **Event and commit:** `GiftEventSubscriber` dispatches in `postFlush`, inside the transaction; the window CLS-4434 accepts applies to `completed` as well.
- **Deploy order:** statistics ([CLS-4938](https://celesta.atlassian.net/browse/CLS-4938)) deploys before this, so the first `completed` event is counted and not dropped by today's `event_promotion` key. Nothing calls the edit until the backoffice ([CLS-4942](https://celesta.atlassian.net/browse/CLS-4942)) ships.

## Dependencies

- Depends on: [CLS-4434](https://celesta.atlassian.net/browse/CLS-4434) (PR #592) — `canceled`, `gift_update`, `GiftService`, `findPlayerGiftForUpdate`. Merged into this branch while #592 is open (task 1).
- Depends on: [CLS-4935](https://celesta.atlassian.net/browse/CLS-4935) — celesta-constants branch `CLS-4935` with `GiftConstants::STATUS_COMPLETED` and the `completed` transition from `claimed`. Required here as `"lancasters/constants": "dev-CLS-4935 as 1.371"`; the repin to the released tag follows once the lead announces it.
- Depends on: [CLS-4938](https://celesta.atlassian.net/browse/CLS-4938) — statistics counts gifts at completion; it deploys before this.
- Blocks: [CLS-4942](https://celesta.atlassian.net/browse/CLS-4942) — the backoffice proxies call `gift_update` with `{"status":"completed"}` or `{"amount":…}`, pass the 400 and 404 back, write `gift_completed` from the returned gift, and write `gift_value_edited` with `previousAmount` as the old value and `amount` as the new one, skipping it when they are equal.
- Related to: [CLS-4940](https://celesta.atlassian.net/browse/CLS-4940) (domain list of claimed and completed gifts, same repository, its own branch), [CLS-4936](https://celesta.atlassian.net/browse/CLS-4936) (job-library activity events, used by the backoffice only).
- Related to: [CLS-4770](https://celesta.atlassian.net/browse/CLS-4770) — adds `sourcePromotionId` to `Gift.php`, `GiftController.php`, `tests/Builder/Gift.php` and `GiftControllerTest.php`, with migration `Version20261117120000`. This plan adds no migration; whichever branch merges second resolves the text conflicts in those files.

## Decisions

- Complete is the `completed` transition on the existing `gift_update` operation, not a new endpoint — Lucas Franco, 2026-11-17.
- Concurrency: the CLS-4434 row lock, no version column. Two edits both pass in order, each response carries the amount it sent, the last is stored; a transition after any action fails on the state machine; each successful action is reported — Lucas Franco, 2026-11-17. The parent's criterion "the second gets an error" does not hold for two edits: pending product owner confirmation.
- Edit to the current amount: 200 with no `gift_value_edited` event; here, nothing is written and `previousAmount` equals `amount` so the backoffice can skip the event — Lucas Franco, 2026-11-17.
- `currency` in the edit body: 400, like any field other than `amount`; the currency never changes — drafter, from the code (the form refuses extra fields); Lucas Franco delegated the call, 2026-11-17.
- Edit value on the same `PATCH`, chosen by the `amount` key, through a request model and its own form, because the `#[Workflow]` constraint on `Gift` refuses an unchanged status — drafter, from the code.
- The edit response adds `previousAmount`, read under the lock, so the backoffice's `gift_value_edited` carries the true old value even when two edits run together — drafter, from the code.
- Value rules are the offer's, shared through one constraint — from the parent (greater than 0, at most 2 decimals) and `Model/Request/Gift.php`.
- Gifts recorded before the release get no special rule: edited, completed and canceled like any other — Lucas Franco, 2026-11-17.
- `offered` is not a backend status; nothing here handles it — Lucas Franco, 2026-11-17.
- Statistics deploys before the promotion's complete — Lucas Franco, 2026-11-17.

## Out of Scope

- The domain gift list for Gift checkout ([CLS-4940](https://celesta.atlassian.net/browse/CLS-4940)).
- Permissions and the `gift_value_edited` / `gift_completed` activity events (backoffice).
- `completed_by`, `completed_at`, order reference, delivery data.
- Editing name, currency, reason or description; bulk actions.
- Any transition out of `completed`.
- A migration: no column changes.

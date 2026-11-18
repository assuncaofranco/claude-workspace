# CLS-4163 — answers for the plan phase

Paste the block below when `/sdd-plan CLS-4163` asks its questions. Every answer is decided by Lucas.

---

All answers below are decided by Lucas Franco.

**Entity and storage**
- The reason's label column is `name` (varchar 64), like `Tag`, `RewardConfiguration` and `Gift`.
- Soft delete uses Gedmo `SoftDeleteable`, as `RewardConfiguration` does.
- `gift.reason_id` is a nullable FK to the reasons table. Reasons are never hard deleted, so the FK is plain.

**Duplicate check**
- The duplicate check runs in form validation (`UniqueEntity` on `domainId` + `name`) and returns a 400 validation error on `name`, like any other field error. The softdeleteable filter keeps deleted reasons out of the check. It follows the column collation (`utf8mb4_unicode_ci`): case- and accent-insensitive.
- Whitespace is trimmed by the form, so a blank name is an empty name.

**Endpoints**
- Create, soft delete and list, all scoped by the domain in the path.
- Deleting an already deleted, unknown or other-brand reason returns 404, as in other deletes.
- The list uses the standard query type: `order`, `limit` and `offset` are optional; without `limit` it returns every reason of the brand, deleted ones included with `deletedAt`.
- Permission is enforced by the backoffice, as for every promotion endpoint.

**Showing deleted reasons**
- Every query that returns a gift disables the softdeleteable filter and fetches the reason in the same query, as `BonusRepository` does for deleted reward configurations: gift list, `findOneByIdempotencyKey`, and the idempotency race winner in `GiftController`. A gift always shows its reason's name, deleted or not.
- A replayed offer returns the original gift with its reason, deleted or not.

**Offer gift**
- `reasonId` is optional. Unknown, deleted or other-brand ids return 400 on `reasonId` and no gift is created.
- The `reason` field stays in `GiftType`, unmapped and ignored, until the backoffice no longer sends it. A follow-up removes it.

**Gift responses**
- Gifts expose `reasonId` and `reasonName`; `reason` is no longer returned. Changing `reason` from string to object would break the backoffice reader, so the keys are new.

**Migration**
- Creates the reasons table, adds `gift.reason_id` with its FK, seeds, and deletes the existing gifts in the same migration.
- Seed: "seed every domain". Promotion has no domain table, so the migration seeds Birthday, Christmas, Easter and Valentine's day for every brand found in `player`, `promotion_configuration` and `gift`. A brand created afterwards starts with an empty list, a state the spec already supports, and its operators add their own reasons from the administration section.
- Existing gifts are deleted, as the spec states: they are test data. Seeded names are in English; label translation is out of scope.
- The `gift.reason` column stays until the follow-up, so this release can be rolled back.

**Follow-up (after the backoffice release)**
- Remove `reason` from `GiftType`, from the `Gift` entity, and drop the column.

**Contract consumers**
- celesta-qaa-proteus gift payloads move from `reason` to `reasonId` / `reasonName` (request and response).

**Checks the platform tests must cover** (request → expected result)
- offer with an active reason of the brand → 201; gift list returns its `reasonId` and `reasonName`
- offer without `reasonId` → 201; `reasonId` and `reasonName` null
- offer with `reason: "birthday"` and no `reasonId` → 201; gift without reason
- offer with an unknown, a deleted, or another brand's reason id → 400 on `reasonId`; no gift created
- replay of an offer whose reason was deleted afterwards → 200 with the original gift and the reason's name
- create a valid name → 201; listed with `deletedAt` null
- create `""` → 400; 64 chars → 201; 65 chars → 400
- create a duplicate of an active reason, same or different case → 400
- create the name of a deleted reason → 201 with a new id; old gifts keep the old id
- create a name that exists only in another brand → 201
- delete an active reason → listed with `deletedAt` set; delete it again → 404; delete another brand's or an unknown id → 404
- list returns active and deleted reasons of the brand only; every field sorts asc and desc; without `limit` returns all
- after the migration every brand lists the four seeded reasons, and no gift from before the migration remains
- gift with a reason deleted afterwards still returns that reason's name

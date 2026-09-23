---
name: custom-attributes-bundle-mechanics
description: "How celesta/custom-attributes-bundle actually persists and resolves custom attributes — config vs. value tables, default_value fallback"
metadata: 
  node_type: memory
  type: project
  originSessionId: 58764f81-09fb-467a-bc18-586ea7655178
  modified: 2026-08-18T14:19:54.957Z
---

`celesta/custom-attributes-bundle` (used by game, player/customer, reward_configuration, and others) always splits into **two tables per integration**:

1. **`<asset>_custom_attribute_configuration`-style shared table `custom_attribute_configuration`** (one generic table, shared across ALL asset types): `id, domain_id, asset (full PHP class name, not the alias string), name, default_value, type`. Unique on `(name, asset, domain_id)`. This is the *definition* — not tied to any specific asset instance.
2. **A per-asset satellite table** (e.g. `reward_configuration_custom_attribute`, `game_custom_attribute` — one dedicated table per asset type, not shared): `id, custom_attribute_configuration_id (FK), asset_id (FK to the actual asset row), value`. This is the *value*, one row per (config, specific asset instance) that ever got an explicit PATCH.

**Key mechanics (verified by reading the bundle source, not the README):**
- Alias→class resolution: `CustomAttributeConstants::CUSTOM_ATTRIBUTE_ASSOCIATIONS[$alias]` (from `lancasters/constants`) gives the class name; the satellite entity class is then derived from that asset's own Doctrine `customAttributes` relation metadata (`CustomAttributeHelper::getCustomAttributeRepositoryByAssetAlias`) — not a second static alias→satellite mapping.
- Setting a value (`PATCH .../custom-attribute/{name}`): the client sends **name**, never a config id. The config row is resolved server-side by `(asset class, domainId, name)`. `AbstractCustomAttributeRepository::getOrCreate()` then upserts the satellite row for that specific asset instance.
- **Reading falls back to `default_value`** (`CustomAttributesDenormalizer::customAttributesDenormalize`): on GET, it loops over *every config* defined for that domain+asset type, and for each one checks whether a satellite row exists for *this* asset instance — if yes, use its `value`; if no, use the config's `default_value`. So every asset instance implicitly has every configured attribute at its default until explicitly overridden — you never need to backfill satellite rows for existing instances when adding a new attribute config.
- `value` is a plain `?string` column (VARCHAR 255) end to end (entity, form is `TextType`) — **no array/JSON support**, only `type: string|image` (an enum with just those two cases).
- Writing (`save()`) also touches `$asset->setUpdatedAt()` unconditionally — the asset entity must have that method (see [[project_custom_attributes_reward_configuration]] for the crash this caused when RewardConfiguration didn't have it yet).

**Where the data shows up — two different behaviors, verified live (2026-08-18):**
- The asset's own single-resource response (`RewardConfiguration::jsonSerialize()`, i.e. `GET/POST/PATCH /reward-configuration/{id}`) includes a `customAttributes` array automatically — but it's the **raw satellite collection**, only attributes that were explicitly PATCHed for that instance. No default-value fallback here.
- Only the bundle's own dedicated endpoint (`GET .../{assetAlias}/{assetId}/custom-attributes`, via `CustomAttributesController` + `CustomAttributesDenormalizer`) merges in `default_value` for configs never explicitly set on that instance. The asset's own serialization does NOT go through the denormalizer.
- The list endpoint (`GET /reward-configurations`) never shows custom attributes at all — filter-only, per the DTO projection.

See [[project_custom_attributes_reward_configuration]] (task memory) for the concrete CLS-1746-CLS-2008 implementation on `reward_configuration`.

---
name: custom-attributes-reward-configuration
description: "Ticket CLS-1746-CLS-2008 scope, sequencing, and cross-service alias-collision gotcha for reward_configuration custom attributes"
metadata: 
  node_type: memory
  type: project
  originSessionId: d31ace76-63e6-4839-9fe8-5e67b667dc85
  modified: 2026-08-03T13:36:45.785Z
---

Ticket **CLS-1746-CLS-2008** implements `celesta-custom-attributes-bundle` for `RewardConfiguration` in `celesta-promotion`, mirroring [[project_gateway_routing_pattern]]-style exploration of the `celesta-game` implementation. Scope also adds a list-filter feature: `customAttributes[]=<name>:<value>` inside the existing `filter` query object (not a bare top-level query param — this codebase's API convention nests all filters under `filter`, see `RewardConfigurationController::getRewardConfigurations` + `FilterType`).

**Why:** `reward_configuration` (celesta-promotion) is the new-system replacement for `BonusModel` in `celesta-wallet` (`App\BonusBundle\Entity\BonusModel`) — same migration lineage as [[project_cel7576_cls848_status]] (BonusModel → RewardConfiguration). The ticket description's mention of "bonus" refers to this **legacy `BonusModel` in celesta-wallet**, NOT the `Bonus` entity in celesta-promotion (table `bonus`, FK to `reward_configuration`, no own `domainId`) — those are two different things and easy to confuse.

**Sequencing (corrected again 2026-08-03 — wallet phase aborted):**
1. **Done:** celesta-promotion / `RewardConfiguration` — full implementation (bundle install, migration, entity wiring, filter), merged with master cleanly, fully tested (1433 PHPUnit + 889 Behat scenarios green).
2. **Wallet phase (celesta-wallet / `BonusModel`) — ABORTED**, not just deferred. User explicitly decided not to build the emergency-rollback-readiness version there after all. Do not act on any earlier note suggesting wallet work is "next" or "right after promotion" — that plan was reversed.
3. Backoffice feature-flag wiring — status unclear now that wallet is aborted; don't assume it's still planned without checking with the user first.

**Cross-service alias gotcha (important, found while implementing, kept for reference in case wallet work is ever revisited):** `CustomAttributeConstants::CUSTOM_ATTRIBUTE_ASSOCIATIONS` is a single static alias→class array shipped as one shared `lancasters/constants` package to every service. `CustomAttributeHelper::getAssetRepositoryByAssetAlias()` resolves `$assetAlias` straight to that hardcoded class string and calls `$em->getRepository($class)` — so the **same alias cannot map to two different classes** depending on which service reads it. If wallet work ever resumes, promotion and wallet would need **two distinct aliases** (`reward_configuration` for promotion; something new, NOT reused, for wallet's `BonusModel`) — not the same alias pointing at different classes per service.

**How to apply:** The `bonus_model` alias/class constants that were pre-reserved in `celesta-constants` for the wallet phase were **removed** (commit `f81acb6`, same `CLS-1746-CLS-2008` branch) once the user aborted that phase — `celesta-constants` now only carries the `reward_configuration` entry. If wallet work resumes later, re-add a fresh alias then (don't assume `bonus_model` is still reserved).

**Second gotcha, found via live curl testing (not in the bundle README or `AssetInterface`):** `celesta/custom-attributes-bundle` v2.4's `AbstractCustomAttributeRepository::save()`/`delete()` unconditionally call `$asset->setUpdatedAt(new \DateTime())` on whatever entity implements `AssetInterface`, duck-typed (not declared on the interface). `RewardConfiguration` had no `updatedAt` field, so the first real PATCH call 500'd with `UndefinedMethodError` even though `doctrine:schema:validate` and unit tests gave no warning. Fixed by adding a Gedmo-managed `updatedAt` field (same pattern as `createdAt`) + backfilling existing rows. **`BonusModel` (celesta-wallet, next phase) will hit the exact same crash on first PATCH unless it already has `getUpdatedAt()`/`setUpdatedAt()` — check for this upfront instead of rediscovering it live.** General lesson: this bundle's real runtime contract is wider than `AssetInterface` + the README suggest; a live curl smoke test (not just `schema:validate`/PHPUnit) is what actually caught it.

The `updated_at` fix above was folded into the *same* migration as the original table creation, not a follow-up one — see `global/skills/ticket-code.md` (seção "Corrigir migration no meio do ticket") for the general rule the user gave here.

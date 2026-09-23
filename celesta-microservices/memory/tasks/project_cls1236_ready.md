---
name: project-cls1236-ready
description: CLS-1236 (celesta-scripts) post-migration bonus reconciliation — spec+plan complete and self-contained; ready to implement the script
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

CLS-1236 = post-migration bonus reconciliation script in **celesta-scripts**, branch
**CLS-392-CLS-1236**. After `MigrateBonusDataToPromotion.php` (CEL-6848), wallet rows change
during the migration window; this script syncs Wallet→Promotion (INSERT if missing, UPDATE if
fields differ) in dependency order FRC → reward_configuration → bonus.

**Status:** spec + plan are complete, approved, and now **self-contained** (no need to re-ask for
DDLs/counts). To resume, just read:
- `sdd/CLS-1236.spec.md`
- `sdd/CLS-1236.plan.md` — now includes production row counts, full-scan index analysis, run
  environment (Docker `php` service), and a DDL appendix.

**Still TODO:** create `script/CLS-1236/ReconcileBonusAfterMigration.php` (does not exist yet),
mirroring `script/CEL-6848/MigrateBonusDataToPromotion.php`'s structure/traits.

**Key facts already settled:** keyset Phase 3 on `(updated_at, id)` is covered by
`idx_sub_balance_updated_at` (InnoDB appends PK); no new permanent index needed but EXPLAIN the
window first. `--since` mandatory; `--until` must be before CLS-1044/CLS-1069 sync start. Skip
log for null `bonus_model_id` at `/var/www/app/data/cls-1236-skipped-bonuses.log`. DB params:
`database_url_wallet` (read) / `database_url_promotion` (write).

See [[project_missing_bonus_model_investigation]] (the 23 null-bonus_model_id rows that get skipped).

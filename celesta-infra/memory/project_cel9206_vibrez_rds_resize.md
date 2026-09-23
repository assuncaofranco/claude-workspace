---
name: project-cel9206-vibrez-rds-resize
description: "CEL-9206 — trial db.t4g.small on vibrez-prod-euw3-api RDS, via vibrez-terraform. Status and what's pending."
metadata:
  type: project
  originSessionId: 79aa3c98-fb0c-4187-a15c-e4ac157378b8
  modified: 2026-09-10T23:42:47.970Z
---

Ticket CEL-9206 (service-desk request from Osman): trial `db.t4g.small` instead of `db.t4g.medium` for the prod RDS instance `vibrez-prod-euw3-api` (MySQL 8.4.8, Multi-AZ, account 407401394609, region eu-west-3). This is a "Vibrez" ticket, a separate business line/AWS tenant from Celesta/SB (see [[project_infra_context]]) — not one of the CLAUDE.md Celesta services, and not gated by the `ticket-understand` service ticket-workflow; it's pure infra/Terraform.

**Repo**: `vibrez-terraform` (`git@github.com:celesta-tech/vibrez-terraform.git`), cloned to `/Users/l.franco/Desktop/infra/vibrez-terraform`. Has its own `.claude/commands/spec.md`/`plan.md` (SDD), same pattern as other infra repos.

**Status as of 2026-09-10**: branch `CEL-9206` pushed to origin, PR open, review requested from the team lead. Now a single commit (rebased): changed `instance_class` in `vibrez-prod/rds.tf` from `db.t4g.medium` to `db.t4g.small`. `terraform plan -target=module.rds_vibrez-prod_mysql_api` confirmed clean both before (0 changes, no drift) and after (1 to change, only `instance_class`) — see [[reference_vibrez_terraform_docker]] for how that plan is actually run on this machine.

Originally the branch also carried a commit removing the 4 orphaned `outputs.tf` entries (see "pre-existing bug" below) — dropped by rebase once the team lead independently fixed the exact same thing on `master` as `CEL-9225` ("Remove orphaned SQS outputs from vibrez-prod and vibrez-staging", author Lucas Azevedo — a different person from Lucas Franco, same first name, don't conflate — merged via PR #147, 2026-09-10 11:56 +0100). `git rebase origin/master` auto-skipped our now-identical commit ("previously applied"), then `git push --force-with-lease` updated the remote branch.

**Key technical fact**: this instance has `multi_az = true` and `db_blue_green_update_enabled = true` (the AWS provider's native `blue_green_update` block). So `terraform apply` will drive the resize through an actual RDS Blue/Green deployment automatically, not a plain in-place reboot or a simple Multi-AZ failover — Terraform orchestrates it.

**Pre-existing bug found along the way** (now fixed in commit 1 above, bundled by Lucas's explicit choice rather than reported separately): commit `a141e9f` (`CEL-9177`, by Atit, 2026-09-07) reverted the CEL-9080 SQS-ingest feature but its commit message claimed it removed 4 outputs in `outputs.tf` that its actual diff never touched — leaving master broken (`terraform plan` hard-errors with "Reference to undeclared module") for anyone touching `vibrez-prod` or `vibrez-staging`, independent of this ticket.

**Update 2026-09-10, after the first real apply attempt**: `CEL-9206` merged to master (PR #148), TL (Lucas Azevedo) approved, timing confirmed with Osman, `terraform apply -target=module.rds_vibrez-prod_mysql_api` run for real. It failed — **`db.t4g.small` does not support Performance Insights**, and this instance has `performance_insights_enabled = true`. AWS rejected the Blue/Green update with `InvalidParameterCombination` while updating the Green environment — this happened *before* switchover, so the real (Blue) instance was never touched: confirmed live, stayed `db.t4g.medium`/`available`/`MultiAZ=true` throughout, zero downtime.

The failed attempt left a stray Blue/Green deployment (`bgd-46v1vqdenf8wj3td`) and its Green replica (`vibrez-prod-euw3-api-green-zla6bd`) running in AWS (double cost, no risk). Terraform's `blue_green_update` isn't a tracked resource in state — it's ephemeral orchestration inside the provider's update logic — so a retry can't resume that deployment; AWS also only allows one active Blue/Green per source instance, so the stray one had to be deleted first regardless of which way the decision below goes. Cleaned up via `aws rds delete-blue-green-deployment --blue-green-deployment-identifier bgd-46v1vqdenf8wj3td --delete-target` — had to first `aws rds modify-db-instance ... --no-deletion-protection` on the **Green** instance only (it inherited `deletion_protection=true` from the module; the real Blue instance's protection was verified untouched throughout). Confirmed via `describe-blue-green-deployments`/`describe-db-instances` polling until both disappeared.

Master currently still has `instance_class = "db.t4g.small"` (merged, but never actually applied to the real instance, which is still `medium`) — a deliberate, known mismatch pending the decision below, not a bug like the CEL-9177/CEL-9225 one.

**Decision now pending with the team** (message sent to TL, awaiting reply): disable Performance Insights on this instance and retry the `small` trial, or abandon the trial and revert `instance_class` back to `db.t4g.medium` in master.

Prepped both ways in advance, not pushed:
- Branch `CEL-9206-2` (local only, 1 commit, off master): sets `performance_insights_enabled = false` alongside the existing `instance_class = "db.t4g.small"`. `terraform plan -target=module.rds_vibrez-prod_mysql_api` confirmed clean: 1 to change (both attributes together). **If authorized**: push, PR, merge, apply this.
- **If declined**: discard `CEL-9206-2`, instead revert `instance_class` back to `db.t4g.medium` on master (a code-only fix — no `apply` needed against AWS, since the real instance was never actually changed).

**Workload measured 2026-09-11 (CloudWatch, before the third attempt)** — the `small` is right-sized, not a gamble: `FreeableMemory` steady at ~800 MB free with no downward trend; data in use ~4.9 GB of 30 GB allocated, growing ~60 MB/day (~1.8 GB/month); `LVMReadIOPS` at 0.03-0.07/s with a 0.51 peak over five days, i.e. the disk is barely touched for reads; `DatabaseConnections` (Maximum statistic) peaking at 29 over five days, typical peaks 5-10, against the ~170 ceiling a 2 GiB instance gets — roughly 6x headroom. This database is close to idle. Record these as the trial's baseline: if `LVMReadIOPS` leaves that band or read latency climbs after the resize, that's the signal to go back to `medium`.

**Still pending regardless of the above**:
- `terraform apply` — **never run this without Lucas actively present/driving it**, and never without the team's explicit go on the Performance Insights trade-off specifically (it's a real, product-level decision, not Claude's to make). No CI automation applies this repo's changes (see [[reference_vibrez_terraform_docker]]) — apply is always a manual local run, via the same Docker workaround.

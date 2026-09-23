---
name: project-legacy-terraform-coverage
description: "Which legacy (pre-K8s) services actually have Terraform-managed compute vs. which don't — gap found exploring CMS/backoffice"
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-09T13:01:06.012Z
  originSessionId: fdddf0c0-e789-4ad1-a273-e9aa973d7833
---

Found while Lucas was learning to read the terraform repos (comparing how CMS/backoffice/promotion/segment show up). See [[project_infra_context]] for the general repo table — this is a granular follow-up, kept separate so it doesn't bloat that file.

**Fact:** `celesta-casino-terraform` (the new, K8s-era repo) only has real Terraform-managed RDS/cache for services already migrated to the new generation: `promotion`, `cmsv2`, `scenario`, `contact_v1`, `rundeck`, `flipper`, `etl`. Everything else in that repo — `backoffice`, `game`, `fraud`, `gateway`, `memberzone`, `cms` (v1), `segment` — is just a hardcoded DNS alias (`route53.tf`'s `int_cname_records`) pointing at a pre-existing hostname (`v2-prod-*`). That repo never created or manages those resources; it only labels them.

**Fact:** the real infra for those legacy services lives in a separate repo, `celesta-ops/terraform/`, organized by resource type (`redis/`, `autoscaling/`, `cloudfront/`, `waf/`, `cloudwatch/`, `backend/`) with one `.tf` file per service inside each folder (e.g. `redis/backoffice.tf`).

**Gap found:** `celesta-ops/terraform/autoscaling/main.tf` only defines EC2 Auto Scaling Groups for `payment`, `wallet`, `memberzone`, `gateway`, `game`. `backoffice`, `fraud`, `cms` (v1), and `segment` have a Redis cache there but **no Auto Scaling Group anywhere found on this machine** — their actual compute provisioning isn't tracked in any locally cloned repo (likely hand-created, or older than this Terraform adoption, or defined in a repo not cloned here).

Their OS-level config is Ansible, not Terraform: `celesta-ops/ansible_reworked/host_vars/` has `v2-prod-backoffice` and `v2-prod-backoffice-2`, matching the hardcoded hostnames exactly.

**Why it matters:** if the CEL-8469 drift-reconciliation epic ([[project_cel8469_lrgi_terraform_audit]], currently scoped only to `lrgi-terraform` IAM) ever expands to `celesta-casino-terraform` or `celesta-ops`, the audit has to span both repos — and has to account for at least 4 services (`backoffice`, `fraud`, `cms` v1, `segment`) whose compute isn't in Terraform anywhere found locally, so "no drift" can't even be evaluated for them, only "unmanaged."

**How to apply:** before concluding a service is "unmanaged" or "not in Terraform," check `celesta-ops/terraform` (per-resource-type folders) in addition to `celesta-casino-terraform` — a hardcoded DNS alias in the new repo usually means the real resource is defined in the old one, not that it's undocumented entirely.

**Correction (2026-09-09, see [[project_service_compute_location]] for the full table):** "no ASG anywhere found" was about Terraform *coverage*, not actual compute — don't read it as "doesn't run on EC2." `backoffice`, `fraud`, and `cms` (v1) are now confirmed to run **only in Kubernetes** (ArgoCD Applications live in both prod-1 and prod-2) — their legacy Redis definition in `celesta-ops` is leftover from before migration, not evidence of current EC2 compute. `segment`, by contrast, genuinely still runs on EC2 in quanta-aws (confirmed live via AWS console) despite having no ASG resource in any locally-cloned repo — its actual autoscaling config (if any) lives somewhere not cloned here. Also: `memberzone` in this repo's ASG/Ansible definitions is the **old name for `crm`**, not an unrelated legacy service — `crm` today is Kubernetes-only.

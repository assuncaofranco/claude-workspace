---
name: project-service-compute-location
description: "Per-service compute location for Celesta prod (casino vs SB) — Kubernetes vs legacy EC2 (quanta-aws), verified live 2026-09-09"
metadata: 
  node_type: memory
  type: project
  originSessionId: a19ab806-42d6-4da2-83d4-387d44cf89d6
  modified: 2026-09-09T13:04:58.731Z
---

Verified while testing two hypotheses about where Celesta microservices actually run in production. See [[project_infra_context]] for the account model and [[project_legacy_terraform_coverage]] for the Terraform-coverage angle (a different question: which repo *provisions* a service's data layer, not where its compute runs — the two don't always agree, see the correction below).

**Method:** `kubectl --context celesta-prod-1 get applications -n argo-cd` (casino) and `kubectl --context celesta-anj-prod-1 get applications -n argocd` (SB/prod-2) gave the authoritative live list per cluster (Rollouts/Deployments/CronJobs cross-checked too — most casino services run as Argo Rollouts, not plain Deployments, so `get deployments -A` alone undercounts). Cross-checked candidates for "not in k8s" against `celesta-ops/terraform/{autoscaling,redis}` and `celesta-ops/ansible_reworked/host_vars/` for legacy EC2 definitions. Final live confirmation of quanta-aws (954607206481) instances came from Lucas's own EC2 console screenshots — no local credentials for that account, so this compute can't be queried directly from here.

**Rename caught in the process:** `memberzone` (legacy EC2 name — ASG `memberzone-autoscale-group` in `celesta-ops`, `min_size=0`) is the *old name* for today's `crm` service, not a separate/decommissioned service. crm now runs only in Kubernetes (both prod-1 and prod-2). The old name still surfaces in `celesta-ops` and possibly elsewhere that predates the rename — don't treat a `memberzone` reference as an unknown/dead service.

**Per-service compute (production only — casino=prod-1, SB=prod-2):**

| Service | Casino (prod-1) | SB (prod-2) |
|---|---|---|
| payment | EC2 quanta-aws — confirmed live (`as-payment`, `as-payment-worker`, `v2-prod-payment` instances). ASG `payment-autoscale-group` in celesta-ops tags instances `as-payment` | k8s (`payment-prod-2`) |
| segment | EC2 quanta-aws — confirmed live (`as-segment`, `as-segment-worker`, `v2-prod-segment` instances). No ASG *resource* found in celesta-ops despite the `as-*` naming — its ASG, if any, isn't in a locally-cloned repo | k8s (`segment-prod-2`) |
| notification | EC2 quanta-aws — confirmed live (`as-notification-worker` x2). No ASG or Redis found in celesta-ops for it | k8s (`notification-prod-2`) |
| scripts | EC2 quanta-aws — confirmed live (`v2-prod-scripts`). **Zero IaC footprint found anywhere local** (no Terraform, no Ansible host_vars) — genuinely unmanaged/console-created compute | k8s (`scripts-prod-2`) |
| crm (was memberzone) | k8s only (`crm`) — legacy ASG exists in code at `min_size=0`, no `as-memberzone`/`memberzone`-named instance seen in the quanta-aws screenshots checked | k8s (`crm-prod-2`) |
| sensor | N/A for casino by design — per Lucas, sensor reports bet data to the French regulator (ANJ), a SB-only obligation; absent from casino k8s and celesta-ops is expected, not a gap | k8s, confirmed live (`sensor-prod-2`, Healthy/Synced, BlueGreen `sensor-active`/`sensor-preview` + `sensor-worker`, 77d) |
| wallet, gateway, game | k8s confirmed live (all three). celesta-ops also defines ASGs for these (tags `as-wallet`/`as-gateway`/`as-game`) — **live-or-dead in quanta-aws is unconfirmed**, absent from the screenshots checked so far but those weren't exhaustive | k8s (all three) |
| gamego, celesta-website | k8s only, casino-specific | absent — no Application exists (website) or was ever synced (gamego) for SB |
| casino-gateway | Scaled down since 2024-10-28 (WIP replacement, not live) — no evidence checked either way for a quanta-aws presence | never existed for SB |
| backoffice, backofficefront, fraud, activity, statistics, contact, scenario, cms, cmsv2, auth, docs, document-validator, etl, mcp, promotion | k8s only, confirmed via ArgoCD Applications | k8s only, confirmed via ArgoCD Applications |
| toolgeoip, rundeck | k8s, casino-only | absent for SB |
| sportsbetting | N/A (casino has no betting) | k8s (`sportsbetting-prod-2`) |
| sb-wallet | N/A — SB reuses plain `wallet`, no separate service | (same row as wallet above) |
| brand, shared-libs | N/A — not deployed services (brand = cmsv2 config concept, shared-libs = code library) | N/A |

**Open items:**
- Whether `as-wallet`/`as-gateway`/`as-game` still exist as live quanta-aws instances is unconfirmed either way — the screenshots reviewed didn't cover them.

**How to apply:** when asked "where does service X run for casino/SB," check this table first instead of re-deriving from scratch — but if the answer affects a real decision (not just an audit), reverify live, since celesta-ops's own IaC coverage for the EC2 side is known to be incomplete (see [[project_legacy_terraform_coverage]]).

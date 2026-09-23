---
name: project-infra-context
description: "Context for the Celesta infra repos — Terraform and ArgoCD structure, AWS/GCP accounts, environments, GitOps flow"
metadata: 
  node_type: memory
  type: project
  originSessionId: e2716478-3583-4105-b8c6-b6b65910fe89
  modified: 2026-09-15T09:46:22.376Z
---

# Celesta Infra — Project Context

Working directory: `/home/lucas/Desktop/infra`

**Need to actually run a command against AWS (terraform, aws cli)?** Don't guess at profiles/MFA here — read [[reference_aws_connection]] first. Keeps this file's context small; that one has the live connection mechanics, which change independently of the infra facts below.

## Goal (updated 2026-09-02)
Primary goal is now **studying DevOps hands-on using Celesta's real infra repos** — not the drift-reconciliation project. Lucas cloned 12 infra repos (list below) into `/Users/l.franco/Desktop/infra` (all via `git@github.com:celesta-tech/<repo>.git`, SSH auth already works under his `lucasfranco83` GitHub identity). Local dev-environment repos (`celesta-global-container`, `celesta-sb-global-container`, `celesta-dev`) are deliberately excluded — those live under `celesta-projects` instead, a sibling folder, and are out of scope for infra study. End deliverable per session: an Artifact visualizing repo responsibilities/relationships.

**Why:** Lucas wants to build DevOps fluency grounded in the infra he actually works with, rather than generic study material.
**How to apply:** Always explain concepts as we work, using these repos as the running example. The old drift-reconciliation goal ([[project_infra_context]] AWS account model, environments, services below) is still accurate background — reuse it, don't re-derive — but don't assume it's the active task unless Lucas brings it back up.

## Repos

| Repo | Purpose | Cloud |
|------|---------|-------|
| `celesta-casino-terraform` | Casino infra: EKS, RDS, ElastiCache, ACM, etc. | AWS |
| `celesta-sb-terraform` | Sportsbetting infra | AWS |
| `celesta-terraform-bi` | BI data warehouse (per-brand/env BigQuery), state stored in AWS S3 (`celesta-infra` profile) | GCP |
| `celesta-terraform-operator-bi` | Generic whitelabel BI platform for other operators (GCP project `tlf-bi-project`) | GCP |
| `celesta-argocd` | K8s manifests — casino services (Kustomize, App-of-Apps; legacy `apps/` + newer multi-source `cel-apps/`) |
| `celesta-argocd-parameters` | Per-environment values/secrets (SealedSecrets), 2nd source for multi-source ArgoCD Apps |
| `celesta-sb-argocd` | K8s manifests — sportsbetting services (separate repo due to isolated AWS accounts/region + ANJ regulatory reqs) |
| `celesta-jenkins-config` | Jenkins-as-code (JCasC) + Jenkinsfiles/Groovy shared libs orchestrating build/deploy across services & envs; calls into celesta-argocd (sync/rollout) and terraform repos (plan/apply) |
| `celesta-ci-templates` | Reusable GitHub Actions workflows (`workflow_call`) — CI, terraform plan/apply/drift, releases — consumed by app repos; `examples/` shows callers, never runs itself |
| `celesta-rundeck` | Self-hosted Rundeck (runbook-as-code) — ad-hoc ops jobs (health checks, fraud/payment notifiers, maintenance SQL) for prod-1 only, via bastion ProxyJump |
| `celesta-ops` | Legacy pre-K8s ops: Ansible playbooks for EC2 fleets (v2-prod/preprod hosts), old per-resource Terraform (autoscaling/redis/cloudfront/waf), EC2 ASG deploy scripts, quanta-aws remnants. Superseded by jenkins-config+ArgoCD (K8s path) for most services |
| `celesta-healthchecks` | Dagster + Python service running scheduled SQL data-integrity checks (BigQuery+MySQL) with Datadog alerting; explicit modern rewrite of celesta-rundeck's/celesta-ops's old shell/PHP health checks |

## Confirmed environments (7, from `celesta-argocd-parameters` top-level dirs — CORRECTED 2026-09-02)
`preprod-1, preprod-2, preprod-3, preprod-4` (casino preprod, shared EKS/VPC across tenants), `staging-1` (casino staging), `prod-1` (**casino** prod), `prod-2` (**sportsbetting** prod — NOT a second casino prod despite the name). "vibrez" is a brand/skin inside `cmsv2`, not an environment (other brands: celesta, madnix, wildsultan, demo).

**Correction:** `sb-preprod-1` does NOT exist as a top-level dir in `celesta-argocd-parameters` (previous memory was wrong — verified by direct listing 2026-09-02). `celesta-sb-argocd` itself only has overlays for `prod-2` and `staging-1`, no preprod at all.

Rollout/promotion order (per `celesta-argocd-parameters/CLAUDE.md`): preprod-4 → preprod-1/2/3 → sb-preprod-1 → staging-1 → prod-1 → prod-2.

## AWS account model — CONSOLIDATED 2026-09-09 (canonical version — supersedes all earlier prose/tables in this section)

Lucas's own framing: **3 production environments, 2 logins.** quanta-aws is the odd one out both as a login (own separate credentials, not assumed via celesta-global) and as an environment (no Kubernetes at all, EC2 only).

**By empresa (company) / login:**

| Empresa | Login | Conta(s) AWS |
|---|---|---|
| Celesta (casino) | Login 1 — celesta-global | prod-1 (413101478321, k8s) **+** legado em Login 2 |
| Celesta (casino) | Login 2 — quanta-aws (credencial separada) | 954607206481 — EC2 puro, sem k8s (`payment`, `segment`, `notification`, `scripts` confirmados live; `wallet`/`gateway`/`game` têm ASG declarado em código, live não confirmado — ver [[project_service_compute_location]]) |
| SB/ANJ (sportsbetting) | Login 1 — celesta-global | prod-2 (336536557570, k8s) — sem presença em Login 2, nasceu direto em k8s |

**By ambiente** (every row except quanta-aws and the hub authenticates via `source_profile = celesta-global`, i.e. assumes a role after landing in account `851725549872`):

| Ambiente | Empresa | Conta AWS | Região | Kubernetes |
|---|---|---|---|---|
| prod (legado) | Celesta | 954607206481 (quanta-aws) | eu-west-1 | Não — EC2 puro |
| prod-1 | Celesta | 413101478321 | eu-west-1 (+eu-central-1 alias) | Sim (EKS) — VPC `10.11.0.0/16`, 3 AZs, reference/template stack |
| prod-2 | SB/ANJ | 336536557570 ("celesta-anj-prod-1") | **eu-west-3 (Paris)** | Sim (EKS) — separate account+region for French ANJ data residency |
| preprod-1..4 | Celesta | 852102753749 | eu-west-1 | Sim (EKS, one shared cluster/VPC, tenants isolated via overlays) |
| staging-1 | Celesta | 276726208200 | eu-west-1 | Sim (EKS) |
| sb-preprod-1 | SB/ANJ | 688567272330 | eu-west-1 | Sim (EKS) — domain `octopo-sb-preprod.com`. **Note: this is the cluster existing, not workloads running on it** — see the "Confirmed environments" correction above: no `celesta-argocd-parameters` dir and no `celesta-sb-argocd` overlay exist for it, so nothing has ever been deployed here |
| sb-staging | SB/ANJ | 257394474030 | eu-west-1 | **Não** — bare VPC only (`10.34.0.0/16`, 2 AZs), no EKS/RDS/ingress. No local AWS CLI profile configured for it either (`~/.aws/config` has no `celesta-sb-staging` entry) — not reachable from this machine right now |
| celesta-global (hub) | — (identity + lrgi-terraform's own IAM) | 851725549872 | — | Não — no cluster, IAM-only account. Plain IAM user `lucas.franco` (verified via `aws sts get-caller-identity --profile celesta-global`), not an assumed role — this is where `awsmfa` lands directly, and where `lrgi-terraform` manages IAM for real (44 users, 8 groups, 12 policies — CEL-8732, see [[project_cel8469_lrgi_terraform_audit]]) |
| celesta-infra (org-root shared) | ambas | 502862189489 | eu-west-1 | Não — no cluster. Hosts the shared org-root: Route53, ACM, ECR (all environments' pull roles), IAM (just a `github` user), VPC, EC2 (github-runner + SG), WAF, CloudWatch/Slack alerts, S3 (2 buckets), and does real VPC-peering (accepter + routes, not just a reference) with **prod-1 and staging-1 only** — despite `celesta-terraform-infra`'s CI also configuring a `celesta-preprod` profile, nothing in that repo's code actually uses it (CEL-8719 finding, in progress — see [[project_cel8469_lrgi_terraform_audit]]) |

**Verified 2026-09-15 about the hub (851725549872)**: no EKS ever (the service-linked role AWS would create does not exist), but `AWSServiceRoleForECS` and `AWSServiceRoleForElasticLoadBalancing` do — residue of the unmanaged AI/Bedrock stack. CloudWatch shows zero metrics in AWS/ECS, AWS/ELB, AWS/EC2 and AWS/EKS, so nothing is actually running there. Also: **the account has no CloudTrail trail in any region checked** (9 regions including us-east-1), so there is no durable record of who touches the state bucket or IAM — flagged for its own ticket, nobody decided on it yet. Note the devops group grants only ssm/s3/logs/kms/iam/dynamodb/cloudwatch/cloudtrail/acm, so `ec2`/`eks`/`ecs` reads are denied from a plain user session — use CloudWatch metrics or service-linked roles to infer what runs there.

**Correction to a past number**: earlier notes here said the hub was `271299367485` — that's only a placeholder in a `celesta-casino-terraform/README.md` copy-paste template, never a real profile. `851725549872` is the verified hub.

**quanta-aws detail**: legacy tenant being wound down, Terraform footprint almost empty (only `kafka-acls` + `aws-health-notifications`, in `celesta-casino-terraform/celesta-prod/quanta-aws/prod/`). Linked to prod-1 via the VPC peering connections found in prod-1's own Terraform (`pcx-0b143698caba883b5`, `pcx-0c1d0e3b993d25575` → peer CIDRs `10.0.0.0/16`, `10.1.0.0/16`) — Lucas confirmed this peering IS the "VPN" link (quanta-aws's own VPC/CIDR is console-managed, not in any repo).

**Unclassified, found but not investigated**: `vibrez-staging` (340752794155) and `vibrez-prod` (407401394609) both exist as profiles in `~/.aws/config` (`source_profile = celesta-global`, i.e. Login 1) and a `vibrez-staging` kubectl context exists too. This is a 3rd business line, not Celesta or SB — partially contradicts the older note below that "vibrez" is just a cmsv2 brand/skin (that may still be true for the content layer while ALSO having its own dedicated AWS tenant — not confirmed either way). Don't fold into the Celesta/SB tables above without actually checking; flagged here so it isn't rediscovered from scratch.

## Entry points (confirmed via ArgoCD ingress manifests)
- **Public entrypoint**: `gateway` (PHP monolith, BlueGreen `-active`/`-preview`) and `casino-gateway` (Go, WIP replacement, scaled down since 2024-10-28) — both have ingress manifests across every casino overlay.
- **Admin entrypoint**: `backoffice` / `backofficefront` — separate ingress manifests across every casino overlay.
Both confirmed present in prod-1, staging-1, preprod-1..4 overlays of `celesta-argocd`.

## Per-environment stack (typical, casino prod-1 / sportsbetting prod-2 style)
VPC + NAT/IGW, EKS (managed node groups in prod; Karpenter in preprod), RDS (MySQL per-service DBs + 1 Postgres for etl), ElastiCache Valkey (per-service, ~12-13 clusters), DocumentDB, Elasticsearch (CRM/segment), Kafka/MSK, CloudFront, WAF, ACM, bastion host, ALB + internal haproxy/nginx ingress, backup + backup-restore-testing (Lambda drills), Datadog, EFS, DynamoDB, SSM. DNS: Route53 (casino, sb prod-2) or Cloudflare (sb preprod, other casino envs) — mixed, not standardized.

**Public ingress stack confirmed present** (verified `cloudfront.tf`/`route53.tf`/`waf.tf` exist) in ALL 5 real EKS-workload accounts: preprod, staging-1, prod-1, sb-preprod-1, prod-2. The lone exception is **sb-staging** (`257394474030`), which has only `vpc.tf`/`backend.tf`/`outputs.tf`/`variables.tf`/`terraform.tf` — no EKS, no data stores, no ingress at all, just a bare VPC (`10.34.0.0/16`, 2 AZs, no workloads deployed). "EKS-workload" here means Terraform provisions it — for `sb-preprod-1` specifically this is infra only, see the AWS account model table's note on it (cluster exists, nothing's ever been deployed to it via GitOps).

`prod-1` is the reference/template stack — every other EKS-based environment (preprod, staging-1, sb-preprod-1, prod-2) follows the same module pattern, just smaller/isolated per account.

## GitOps / ArgoCD pattern
Kustomize + App-of-Apps, no Helm. `celesta-argocd` has two generations: legacy `apps/kustomize/{base,overlays}` (single-source, namespace `celesta`) and newer `cel-apps/kustomize/` (namespace-per-env, multi-source Applications pulling manifests from `celesta-argocd` + config/secrets from `celesta-argocd-parameters` at path `<env>/<service>`). **Correction (verified 2026-09-02): the migration is incomplete, not a clean split** — `cel-apps/` multi-source is used ONLY for `preprod-1..4`; `prod-1` and `staging-1` still run the legacy single-source pattern, namespace `celesta`. `celesta-sb-argocd` mirrors the legacy single-source pattern (namespace `celesta-sb`), covering only `prod-2`/`staging-1` (no preprod). SealedSecrets everywhere. Argo Rollouts for BlueGreen (`-active`/`-preview` suffixes, e.g. `gateway-active`/`gateway-preview`).

No single central API gateway: each vertical has its own gateway service (`gateway` — PHP monolith, BlueGreen) fronting most traffic; `casino-gateway` (Go, newer) exists only as preprod-1..4 overlays and was **scaled down 2024-10-28** (in-progress replacement, not live). Individual services also expose their own ingress paths.

## Services (as actually deployed, grouped)
- Core betting: `game` (PHP), `gamego` (Go), `sportsbetting`, `casino-gateway` (WIP, not live)
- Payments/wallet: `payment`, `wallet` (sportsbetting reuses plain `wallet`, not a separate `celesta-sb-wallet`)
- Backoffice/admin: `backoffice`, `backofficefront`, `rundeck` (prod-1 only)
- CRM/marketing: `crm`, `promotion`, `segment`, `notification-worker`, `contact`
- Risk/compliance: `fraud`, `sensor`, `document-validator`, `scenario`
- Content/brand: `cms`, `cmsv2` (multi-brand), `celesta-website`, `docs`
- Data/infra: `activity`, `statistics`, `etl`, `toolgeoip`, `auth`, `mcp`, `scripts`, `gateway`

Note: `celesta-brand` and `shared-libs` from the global service list are not deployed services (brand is a config concept inside cmsv2; shared-libs is a code library). Naming differs from CLAUDE.md's global list in places (`celesta-game-go`→`gamego`, `celesta-cms-v2`→`cmsv2`, `celesta-notification`→`notification-worker`).

## BI / Analytics (GCP)
`celesta-terraform-bi`: BigQuery datasets per brand/env (`celesta-325419` prod-1, `celesta-preprod-1..4`, `celesta-staging-1`, `casino-prod-cs`, `sportsbetting-prod-1/preprod-1/staging-1`) — datalake tables for activity/bonus/game/payment/fraud/wallet domains, fed from the AWS platform (exact ETL pipeline not defined in this repo). `celesta-terraform-operator-bi`: separate generic whitelabel BI platform, single GCP project `tlf-bi-project`.

## SDD Workflow in this repo
- `/spec [description]` → creates `_specs/[TICKET].md`
- `/plan [TICKET]` → creates `_plans/[TICKET].md`
- Templates: `_specs/template.md` exists; plans have no template

## Architecture diagram (drafted 2026-07-09, for Gemini image generation)
Full landscape mapped and turned into an image-gen prompt for Gemini. Agreed representation model (reuse for future diagram updates):
- Two groups: "celesta-global" (contains preprod, staging-1, prod-1, sb-preprod-1, sb-staging, prod-2) and "quanta-aws" (separate, legacy).
- `prod-1` drawn FULL detail as the template (entry stack, EKS, gateway=PUBLIC ENTRYPOINT w/ BlueGreen badge, casino-gateway=WIP dashed, backoffice=ADMIN ENTRYPOINT, 40+ microservices cluster, data layer, bastion/datadog). All other EKS accounts (preprod, staging-1, sb-preprod-1, prod-2) drawn COLLAPSED, tagged "same stack as prod-1" — full detail repeated 6x made the image illegible/glitchy (duplicated content, broken borders) when first attempted.
- `sb-staging` drawn as bare VPC only (no stack).
- `quanta-aws` drawn with plain VM icons + "not managed in Terraform / drift" warning badge, connected to prod-1 via the VPC peering (`pcx-0b143698...`, `pcx-0c1d0e3b...`) routed along the outer margin (not through the sportsbetting row).
- GitOps panel (ArgoCD + 3 repos) at the bottom, numbered arrows 1-6 in promotion order, with arrows 1 & 2 (preprod-4, preprod-1/2/3) both pointing at the same preprod box.
- BigQuery arrow must originate from Kafka icons inside prod-1/prod-2, not from the GitOps panel.
Lesson learned: dense nested diagrams (full stack repeated per environment) break image-gen legibility — always collapse repeated patterns to a tagged reference after the first full example.

## Next steps
- Get AWS credentials configured (`celesta-prod-1` AWS profile)
- Run `terraform init` then `terraform plan` in `celesta-prod/prod-1/`
- Compare plan output with actual AWS state to identify drift

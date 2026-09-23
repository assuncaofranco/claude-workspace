---
name: reference-infra-repos
description: "Exact list of infra repos and their purpose — Terraform, ArgoCD, and environment structure"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 2af80ad8-843e-4a98-9876-9b91b0598a40
  modified: 2026-08-11T10:22:37.185Z
---

## Terraform repos

| Local folder | GitHub origin | Purpose |
|---|---|---|
| `celesta-casino-terraform` | `celesta-tech/celesta-casino-terraform` | Main casino infra (EKS, RDS, ElastiCache, ACM, CloudFront, etc.) |
| `celesta-terraform-infra` | same as above | Duplicate local clone with different folder name — IGNORE |
| `celesta-sb-terraform` | `celesta-tech/celesta-sb-terraform` | Sportsbetting infra |
| `celesta-terraform-bi` | `celesta-tech/celesta-terraform-bi` | BI infra (BigQuery, ETL) |
| `celesta-terraform-operator-bi` | `celesta-tech/celesta-terraform-operator-bi` | BI operator |

## ArgoCD repos

| Repo | Purpose |
|---|---|
| `celesta-argocd` | K8s manifests for all main services |
| `celesta-argocd-parameters` | Per-environment values (prod-1, prod-2, preprod-1..4, staging-1, vibrez, sb-preprod-1) |
| `celesta-sb-argocd` | K8s manifests for sportsbetting |

## Environments in celesta-argocd-parameters

- `prod-1` — production cluster 1 (main)
- `prod-2` — production cluster 2
- `preprod-1` to `preprod-4` — pre-production
- `staging-1` — staging
- `vibrez` — specific brand/environment
- `sb-preprod-1` — sportsbetting pre-prod

## Terraform state buckets (celesta-casino-terraform)

- **prod:** S3 `celesta-prod-terraform-new`, DynamoDB lock, AWS profile `celesta-prod-1`, region `eu-west-1`
- State is per-environment: each env folder (`celesta-prod/`, `celesta-staging/`, `celesta-preprod/`) has its own `backend.tf`

## AWS accounts

- **Quanta** (account 954607206481, alias `quanta-aws`) — the OLD work AWS account, no Kubernetes.
- **lrgi-global** (account 851725549872) — the NEW work AWS account, has Kubernetes (this is the account behind the `celesta-global`/`celesta-global-mfa`/`celesta-preprod-1` etc. profiles in `~/.aws/config`).
- Repos are being migrated from Quanta to lrgi-global gradually, as of 2026-08-11 — expect to see both account IDs referenced in older docs/scripts until that finishes.

## Key context

Terraform is significantly out of date — changes were applied directly in the AWS console. The goal is to reconcile `.tf` files with actual AWS state. Primary method: run `terraform plan` per environment and share output here for analysis.

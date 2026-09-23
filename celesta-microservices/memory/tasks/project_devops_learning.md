---
name: project-devops-learning
description: User is new to DevOps and learning through hands-on infra work; context for how to explain and teach while executing tasks
metadata: 
  node_type: memory
  type: project
  originSessionId: 2af80ad8-843e-4a98-9876-9b91b0598a40
---

User is transitioning into DevOps and wants to understand the infrastructure while working on it — not just execute tasks blindly.

**Why:** Learning by doing; needs explanations of concepts (Terraform, ArgoCD, K8s) in context as they come up, not upfront theory dumps.

**How to apply:** When touching infra files, briefly explain what a resource does and why it exists before changing it. Don't assume prior K8s/Terraform knowledge. Treat each task as a teaching moment without being patronizing.

## Current infra focus

See [[reference-infra-repos]] for the full repo map.

Key structure:
- Terraform manages AWS base infra (EKS, RDS, ElastiCache, ACM, etc.)
- ArgoCD deploys services onto the K8s clusters
- `celesta-argocd-parameters` holds per-environment values (prod-1, prod-2, preprod-1..4, staging-1, vibrez, sb-preprod-1)
- Terraform is significantly out of date — AWS console changes were applied directly and never reflected back in `.tf` files

## First task: reconcile Terraform with AWS reality

Status: **not started** — no `terraform plan` output yet, no specific drift identified.

Approach when ready:
1. Run `terraform plan` per environment and share output
2. Identify drift resource by resource
3. Either update `.tf` files or run `terraform import` for untracked resources
4. Start with `celesta-casino-terraform/celesta-prod` (prod-1, AWS profile `celesta-prod-1`, region `eu-west-1`)

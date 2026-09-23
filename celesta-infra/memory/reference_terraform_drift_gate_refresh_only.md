---
name: reference-terraform-drift-gate-refresh-only
description: "An apply-on-merge drift gate must use `terraform plan -refresh-only`, never a plain plan, or it blocks every merge"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-15T14:40:32.468Z
---

A gate that runs before `terraform apply` and fails on `-detailed-exitcode == 2`
must pass `-refresh-only`. A plain `terraform plan` returns 2 for the change
being applied itself, so the gate would block every merge.

- plain plan: "does AWS match the code" — right for a daily drift cron
- `-refresh-only`: "did AWS move away from the state" — right for an apply gate

Neither writes state, so both are safe on a schedule against production.

Complementary check, and it is Terraform's own, not something to build: applying
a saved plan file fails if the state serial changed since the plan was made.
That catches another PR merging in between; it does NOT catch manual AWS changes,
which is exactly the gap `-refresh-only` fills.

Used in `lrgi-terraform/.github/workflows/{drift,apply}.yml` — see
[[project-cel8469-lrgi-terraform-audit]].

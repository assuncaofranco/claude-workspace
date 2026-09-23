---
name: reference-vibrez-terraform-docker
description: "How to run terraform locally in vibrez-terraform (and likely other same-vintage repos) on Apple Silicon — Docker workaround, no CI automation in this repo"
metadata:
  type: reference
  originSessionId: 79aa3c98-fb0c-4187-a15c-e4ac157378b8
  modified: 2026-09-10T15:16:30.069Z
---

`terraform init`/`plan`/`apply` fail natively on Lucas's Mac (arm64/Apple Silicon) for `vibrez-terraform`'s `vibrez-prod` and `vibrez-staging` roots — not a code bug, a provider platform gap. `modules/eks` and `modules/eks_node_group` depend on `hashicorp/template` (archived by HashiCorp years ago, superseded by the builtin `templatefile()`), which was never built for `darwin_arm64`. No terraform CLI version fixes this — the CLI just orchestrates downloading pre-built provider binaries, and this specific one was never compiled for this architecture. Same root cause likely applies to `celesta-casino-terraform` (same modules/eks copy, confirmed via `.terraform.lock.hcl` only ever locking non-arm64 platforms).

**Real fix** (not done, out of scope for a normal ticket): swap `template_file` data sources for `templatefile()` inside `modules/eks`/`modules/eks_node_group`. Touches the EKS module shared by prod+staging — bigger blast radius than most tickets, do as its own dedicated change.

**Workaround**: run terraform inside a Linux/amd64 Docker container instead of on the Mac directly — same code, same requirement, but a linux/amd64 "machine" asking for providers gets a build that actually exists.

**`vibrez-terraform-check` is a standing container — permanent, never on a timer, never destroyed.** An earlier version of this note had it started with `sleep 3600`, on the assumption it was only needed briefly. That assumption caused a real incident (2026-09-10): the container died mid-`apply` because the 1-hour timer ran out while a Blue/Green deployment was still in flight, killing the Terraform CLI process, leaving an orphaned Blue/Green deployment + Green replica in AWS and a stuck DynamoDB state lock (recovered via `describe`-then-`delete-blue-green-deployment --delete-target` and `terraform force-unlock`, see [[project_rds_bluegreen_lessons]]). **Never give this container a time limit again** — idle cost is negligible, and a `terraform apply` (especially a Blue/Green one) can legitimately run 15-40+ minutes.

Check first whether it's already running (`docker ps --filter name=vibrez-terraform-check`) — reuse it, don't recreate. Only if it's genuinely gone (Mac/Docker Desktop restart, or someone stopped it) recreate with:

```
docker run -d --name vibrez-terraform-check --platform=linux/amd64 \
  -v "/Users/l.franco/Desktop/infra/vibrez-terraform:/workspace" \
  -v "$HOME/.aws:/root/.aws:ro" \
  -w /workspace/vibrez-prod \
  -e AWS_PROFILE=vibrez-prod \
  --entrypoint sh \
  hashicorp/terraform:1.9.5 -c "tail -f /dev/null"
```

Then Lucas works inside it via **Docker Desktop's own Containers → exec/terminal tab for that container** — not `docker exec -it ... sh` typed in his own Mac terminal (he found juggling both terminals confusing; asked to always be pointed at the container's own terminal instead). Inside, `terraform` is on PATH and CWD is already the right root, so commands are just `terraform plan ...` directly.

**Second, unrelated gotcha inside the container**: plain `terraform plan` (no `-target`) fails differently — the `kubernetes` provider tries to auth to the EKS cluster's aws-auth configmap via an exec credential plugin, and the minimal container has no `aws` CLI or `~/.kube/config` for that. Sidestep by scoping with `-target=<module or resource address>` (e.g. `-target=module.rds_vibrez-prod_mysql_api`) — validated safe/expected for a single-resource change like an RDS instance class edit.

**No CI automation exists for this repo** — `vibrez-terraform` has no `.github/workflows/` at all (checked directly), unlike what `celesta-ci-templates`' reusable `terraform-plan.yml`/`terraform-apply.yml` would suggest. So both the reviewed `plan` and the real `apply` have to be run manually/locally (via this same Docker container) — there's no apply-on-merge gate catching this repo. See [[project_infra_context]] for the repo list and [[reference_aws_connection]] for the AWS session mechanics this depends on (`AWS_PROFILE=vibrez-prod` needs a valid `awsmfa` session already sitting in `[celesta-global]`).

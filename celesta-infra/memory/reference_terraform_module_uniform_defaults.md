---
name: reference-terraform-module-uniform-defaults
description: "Reusing a shared module's for_each/uniform defaults across a list of found-live resources isn't reflection — each one needs its own live values checked first"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a19ab806-42d6-4da2-83d4-387d44cf89d6
  modified: 2026-09-18T08:22:39.657Z
---

Found in CEL-8720 (celesta-terraform-infra), caught by review (Fable), verified live before fixing — 7 of 7 flagged mismatches were real.

**The mistake:** when reflecting live-but-unmanaged resources into code, it's tempting to reuse an existing shared module call (or a for_each over a single set of arguments) just because the *shape* matches what's already correctly declared. It doesn't follow that the *values* match — a module that applies one policy/tag/setting uniformly to every item in a list will, on `apply`, force every item in that list to that single value, silently changing whichever ones don't already match it.

Concretely, in this repo's `./modules/ecr`, `./modules/s3`, `./modules/iam`:
- `aws_ecr_repository_policy` — one `ecr_policy` applied to every repo in `ecr_repo_names`. 17 of 20 newly-found repos had an extra IAM principal live that the shared policy didn't have; applying would have revoked it.
- `aws_s3_bucket_ownership_controls`/`_versioning`/`_public_access_block` — hardcoded per module, no per-bucket override for versioning. 3 buckets were live `BucketOwnerEnforced` (stricter); the module's `expected_bucket_owner="BucketOwnerPreferred"` copied from already-correct buckets would have downgraded them — one of them this root's own backend bucket. A separate bucket had a deliberate public-read policy that the module's public-access-block defaults would have silently disabled without touching the policy document.
- `aws_iam_user.tags = var.tags` — one tag map applied to every user in `users_extended`. Two newly-found users each had their own distinct (or empty) live tags that the shared map would have overwritten.

**Why `import` alone doesn't catch this:** importing a resource makes state match live *at that moment*. The drift only shows up on the *next* plan, once the module's uniform argument is compared against each individual resource's live value — by which point the import already happened. Checking "does `terraform plan` show 119 to add, 0 to change" before import proves the code is syntactically fine and the resources don't already exist in state; it proves nothing about whether the values inside a for_each are individually correct, because pre-import every one of them shows as "to add" regardless.

**The fix, generalizable:** before reusing a shared/uniform-default module for a *batch* of found-live resources, check each one's actual live configuration individually first — not just that the resource exists, and not just a sample. Where values genuinely differ across the batch, split into groups that share a value (a second module instance, e.g. `ecr_extra_principal` above) or go fully standalone for outliers. Where checking every member of a large batch isn't practical in the time available, it's better to declare the subset that's actually been checked and leave the rest out of the PR — noted as deferred — than to declare all of it as a group and accept a mismatch you haven't looked for.

**Method that catches this:** for every group (module call driving a for_each, or a shared list), pull the live config for *every member*, not a sample — a script/loop over `aws ... describe/get` per resource, diffed against what the shared argument would produce. The 3 checks that found real issues here were `aws ecr get-repository-policy` (principal count/content per repo), `aws s3api get-bucket-ownership-controls`/`get-bucket-versioning`/`get-public-access-block`/`get-bucket-policy` (per bucket), and `aws iam list-user-tags` (per user) — all cheap, all scriptable across a whole list in seconds.

See [[project_cel8469_lrgi_terraform_audit]] for the broader epic this belongs to, and [[reference_terraform_import_window]] for the related but distinct risk (import timing vs. merge timing) that this doesn't overlap with — that one is about *when* state changes relative to master; this one is about whether the *values* being declared are correct at all, regardless of when they're imported.

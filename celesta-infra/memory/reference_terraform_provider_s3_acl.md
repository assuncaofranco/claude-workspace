---
name: terraform-provider-s3-acl
description: "Why imported S3 buckets show a phantom acl diff on AWS provider < 4.0, the workaround in place, and why upgrading the provider is probably the real and small fix"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-15T09:46:09.140Z
---

Cost a full evening to work out. Read this before touching S3 buckets in any repo pinned to
AWS provider < 4.0.

**The symptom.** An imported `aws_s3_bucket` always shows `+ acl = "private"` (and
`+ force_destroy = false`) in the plan, forever, no matter what the code says. Applying it
fails on any bucket with ACLs disabled: `AccessControlListNotSupported`, and the apply stops
halfway, leaving part of the change applied.

**The mechanism.** On providers below 4.0 the `acl` attribute is `optional` only, with a
provider-side default of `"private"`. The provider never reads the ACL back from AWS (it
cannot map grant lists to a canned name), so after an import the state holds `acl = null`
while the config keeps offering `"private"`. Reality is fine — the bucket is already private —
the disagreement is only between state and intent. Buckets Terraform created never show this,
because the value was written to state at creation.

**Why it cannot be fixed from the caller.** `acl = ""` is rejected by the provider's enum
validation, `acl = null` falls back to the schema default, and removing the line from the
module changes nothing because the default still applies. Verified all three.

**The workaround in place.** `lifecycle { ignore_changes = [acl] }` on the bucket resource in
`celesta-terraform-modules/terraform-aws-tfstate-backend`. It costs nothing in drift
detection, since the provider never read that field back anyway. Upstream issue describing the
exact case: hashicorp/terraform-provider-aws#17791, open since 2021, closed by a stale bot in
2024 with no fix. The only other workaround in that thread is hand-editing state.

**The part I missed, and Lucas caught.** From provider 4.9 the attribute is `optional` AND
`computed`, which is precisely what makes the phantom diff disappear. So for a repo that can
move off `< 4.0`, the real fix may be a one-line change to `versions.tf` plus
`terraform init -upgrade` plus reading the plan — not the module rewrite I had framed as a
project. The deprecated inline arguments (`acl`, `policy`, `versioning`, `logging`,
`replication_configuration`) still exist in 6.x, so upgrading does not break the old module
shape; migrating to `aws_s3_bucket_acl` and friends is cleanup without a hard deadline.

**How to check a provider's behaviour yourself:**

    terraform providers schema -json | python3 -c "import json,sys; d=json.load(sys.stdin); print([v['resource_schemas']['aws_s3_bucket']['block']['attributes']['acl'] for v in d['provider_schemas'].values()])"

    3.76.1  ->  {"deprecated": true, "optional": true}
    6.64.0  ->  {"deprecated": true, "optional": true, "computed": true}

**Safety rule agreed with Lucas:** a genuinely empty plan means apply makes no API calls, so
there is nothing for AWS to reject. Fear belongs to non-empty plans. The only lasting cost of
a major provider bump is that the state schema migration is one-way, so back the state up
first.

Full write-up in `~/Desktop/infra/tickets/CEL-8733/provider-version-reference.md`.
See [[project_cel8469_lrgi_terraform_audit]].

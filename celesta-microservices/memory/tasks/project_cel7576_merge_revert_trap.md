---
name: project-cel7576-merge-revert-trap
description: CEL-7576-2 merge vs master after TL reverted CLS-1058 — revert resurrects deleted NewSubBalance on naive merge; resolved via merge commit 4f963991a that re-asserts the deletion
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

In `celesta-wallet`, the TL merged CLS-1058 (PR #1736, which had absorbed the CEL-7576
migration) into master, then reverted the whole PR via **dc380386a** (PR #1747). The revert
**resurrected all 9 NewSubBalance files and undid the migration** on master.

**The trap (git revert-of-merge):** our CEL-7576/CLS-848 deletion commits became common
ancestors of master (entered via CLS-1058), but the revert `dc380386a` lived only on master.
A naive `git merge` (either direction) silently resurrects NewSubBalance: base=deleted,
ours=deleted, theirs=present(revert) → theirs wins, no conflict marker.

**Key facts that made resolution clean:**
- `git diff <merge-base a1e0f69c7> master` = only **7 infra files** (Makefile, docker-compose.bake/
  test, ops/docker/Dockerfile, ops/docker/config/zz-pcov.ini, PLAN/SPEC-CLS-775_CLS-1191.md) —
  the CLS-1058 merge+revert netted to zero. So master ≡ (pre-1058 master) + those 7.
- Zero overlap between those 7 and the ~60 migration files.

**Resolution (merge commit 4f963991a on CEL-7576-2):** `git merge --no-commit master`, then
rebuild the tree = `git checkout OUR_HEAD -- .` + graft the 7 infra from master + `git rm` the
resurrected NewSubBalance files. Gate: `git diff --cached OUR_HEAD` must show EXACTLY the 7 infra
files. This puts dc380386a in our ancestry with a later deletion on top, so the future PR
`CEL-7576-2 → master` merges clean (verified: 0 conflicts, NewSubBalance stays deleted).

**Why:** a real merge (not `git checkout master -- files`) is required so the revert is an
ancestor and the deletion is "newer" than the revert — otherwise the PR re-triggers the trap.
Do NOT use `git revert dc380386a` (revert-the-revert): it restores the STALE CLS-1058 migration
and reopens the trap on the next merge.

**Env note:** `lancasters/constants` `^1.316` (with `RgLimitConstants`, added by CLS-439-CLS-865 —
a master requirement) must be installed via `make init` or the full PHPUnit suite won't collect.
Validated: full suite OK (1310 tests, 5549 assertions). Push/PR to master is the TL's call.

See [[project-cel7576-review-cleanup]] and [[project_cel7576_cls848_status]].

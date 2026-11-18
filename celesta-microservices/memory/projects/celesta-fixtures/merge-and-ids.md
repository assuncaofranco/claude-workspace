---
name: celesta-fixtures-merge-and-ids
description: "celesta-fixtures tags itself on every master push, so merging is releasing; open PRs share the numbered aliases; backoffice loads it in test too"
metadata:
  node_type: memory
  type: project
  originSessionId: 57fbff35-2b72-4548-8ce7-d938bb9ec755
  modified: 2026-11-10T08:56:31.583Z
---

- The CI tags on every push to master (`release.yml`, no PR trigger, no test suite). So **merge = tag = release**. A fixture that references an entity which isn't on the service's master yet breaks `hautelook:fixtures:load` for everyone who runs `composer update`. Merge only after the service PRs.
- Aliases are numbered (`secondary_permission_N`, `secondary_policy_permission_N`…) and the open PRs claim the next numbers without coordinating. Before picking a number, run `git diff origin/master...<branch>` on every open PR. The Symfony YAML parser refuses duplicate keys, so a bad merge breaks the whole file.
- celesta-backoffice loads these fixtures in `dev` **and** `--env=test` (install.sh), so a new row can change backoffice tests. celesta-promotion loads them in dev only, and its behat tests build their own data.
- **A new backoffice policy breaks 4 backoffice tests**, because they hardcode the policy count: `PolicyControllerTest:38`, `ProfileControllerTest:72` and `:136`, `UserControllerTest:262` (102 in 2026-11). `FixturesTrait` loads the vendor fixtures. Whoever adds a policy has to bump those counts in the backoffice PR that goes in **before** the fixtures (precedent `e731b2669b`, CLS-2594-CLS-3107). Discovered in CLS-4543, where the plan didn't cover it.
- Verifying a branch: `composer require lancasters/celesta-fixtures:dev-<branch>` inside the service container, load, then revert composer.json/lock.
- **A fixture written against a service branch goes stale when that branch moves before the fixtures PR merges.** CLS-4543 shipped `quantity` on the sample gift the same day the CLS-4034 merge removed it from promotion's `Gift`; Socrates caught it in review (2026-11-10) and bounced the ticket to To Do. Before pushing, and again before asking for review, re-read the referenced entities at the service branch's current tip (`git fetch` + `git show origin/<branch>:src/.../Entity/X.php`) and re-run the load.

**Why:** found while planning CLS-4543 (2026-11-09, PR #309): ids 450/486 were already taken by #301/#304/#305, so we went with 460/461 and 496/497.
**How to apply:** any ticket that touches celesta-fixtures. See [[project_stacked_pr_merge_trap]] for the stacked-PR side.

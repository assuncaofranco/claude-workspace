---
name: feedback-local-postman-collections-folder
description: "Ad-hoc/no-ticket Postman collections go in ~/Desktop/celesta-projects/claude-workspace/celesta-microservices/postman/<slug>/, not inside a service repo"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9a03a386-1317-4fcd-b9c2-4cab1e93d2da
  modified: 2026-09-02T09:54:40.066Z
---

When building a Postman collection outside the formal ticket flow — e.g. reproducing a bug found mid-investigation, before any ticket exists — save it to `~/Desktop/celesta-projects/claude-workspace/celesta-microservices/postman/<slug>/<slug>.postman_collection.json` + `<slug>.md`, not into any service's `sdd/_how_to_test/`.

**Why:** these collections aren't meant to be committed on a branch. Lucas asked (2026-09-02, during the CEL-8373-followup change-password-confirmation-email investigation) for a dedicated folder specifically so ad-hoc/local-only collections don't end up polluting a service repo or getting accidentally committed. `_local-postman-collections/` sits as a sibling to the service repos inside `~/Desktop/celesta-projects/`, outside every git repo, so nothing there can leak onto a branch by accident.

**How to apply:** this is now written into the `ticket-postman` skill itself (`~/.claude/commands/ticket-postman.md`, step 5) — when no ticket id exists yet, use a short descriptive slug instead of blocking to ask for one, and save there. Once a real ticket gets filed for the underlying issue, move both files into that service's own `sdd/_how_to_test/<TICKET>/` and rename them to the ticket id. In this ad-hoc mode the skill's normal "test the FEATURE, not the bug" rule does not apply — the whole point of one of these collections can be demonstrating a bug end to end (see [[tasks/project_cel8373_change_password_confirmation_email]] if that memory exists, or the CEL-8373-followup collection itself for the canonical example).

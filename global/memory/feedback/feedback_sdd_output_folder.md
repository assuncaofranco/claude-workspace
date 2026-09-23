---
name: feedback_sdd_output_folder
description: "SDD spec and plan output documents must be saved in the sdd/ folder, not .claude/"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7aedfe78-f16f-450f-b740-38a591b774c8
---

Save spec and plan documents in `sdd/` at the project root, not in `.claude/`.

**Why:** The `.claude/commands/` path is where the template scripts live. The output documents (the actual spec and plan for a ticket) belong in `sdd/`. Putting them in `.claude/` mixes infrastructure with deliverables.

**How to apply:** When creating `spec-<TICKET>.md` or `plan-<TICKET>.md` for any ticket, write them to `<project-root>/sdd/`, creating the directory if it doesn't exist.

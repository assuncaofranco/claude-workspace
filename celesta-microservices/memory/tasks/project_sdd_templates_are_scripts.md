---
name: SDD templates in celesta-gateway are CLI scripts, not format files
description: spec.md and plan.md in .claude/commands/ are skill command scripts, not document templates to fill in
type: project
originSessionId: c2906b35-7daf-4bab-af2c-ca3eb9157cad
---
The files at `celesta-gateway/.claude/commands/spec.md` and `celesta-gateway/.claude/commands/plan.md` are **slash command scripts** that describe a multi-step interactive workflow (check git branch, ask for ticket ID, create files, switch branches, etc.). They are NOT document format templates.

- `celesta-promotion` has an empty `.claude/` directory — no templates exist there.
- When the user provides a full ticket description, that description IS the spec. No need to invoke `/spec` or read these files as format guides.
- The plan format to use: Overview, Architecture & Design, Implementation Tasks, File Changes, Testing Strategy, Edge Cases, Open Questions.

**Why:** Reading these files in future sessions wastes tokens since they don't define the document format — they define a CLI skill workflow.

**How to apply:** When a user provides a ticket description for a celesta-promotion or celesta-gateway feature, skip reading spec.md/plan.md and proceed directly to codebase exploration and planning.

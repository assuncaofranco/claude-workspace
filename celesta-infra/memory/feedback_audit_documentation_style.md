---
name: feedback-audit-documentation-style
description: How Lucas wants drift/inventory audit findings written up — verified against how he corrected drafts across the CEL-8732 audit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-09T10:47:44.965Z
---

Write audit/findings documents as tables of fact, not prose. Every claim needs a command that produced it, verifiable independently.

**Why:** across many rounds of revision on the CEL-8732 (lrgi-terraform) drift audit, every AI-sounding sentence ("Also:", "worth raising", explanatory paragraphs under a table) got flagged as noise or as hiding an ambiguity the table alone would have shown clearly. He explicitly said AI-flavored verbosity creates reader bias/rejection, even when everyone knows AI was used — the fix is human simplification, not hiding AI involvement.

**How to apply:**
- One table per category of finding (users, policies, roles, groups). Columns should let the reader see the mismatch directly — never mix two different questions (e.g. "does this user exist" and "does this user have this permission") in one column.
- No narrative connective tissue ("Also:", "In practice:", "It's worth noting"). If a sentence doesn't answer a question the table itself raises, cut it.
- State only what matches (a short bullet list, "nothing to do here") and what doesn't (the tables). No middle ground / partial-credit framing.
- Before asserting anything as a finding, verify with a live command — do not reconstruct from memory of an earlier response. He caught several of my own claims that were wrong when re-checked (an MFA "gap" that turned out to be a different-but-equivalent enforcement style, a "redundant" policy that turned out to add 4 real actions for one group, a security observation that mixed up "content differs" with "entirely absent from code").
- For anything going to a person who "doesn't read documents" (e.g. a VPoE), compress further: one-line problem, one-line pattern being violated, one direct question. See [[project_cel8469_lrgi_terraform_audit]] for the exact final format he converged on.
- When two things could be fixed (e.g. "reflect as-is" vs "actually fix"), always ask which — never assume the safer non-mutating option is what he wants, but do flag clearly which option requires a real AWS change vs which is state-only/reversible.
- For any binary framing, check whether a genuine third option exists — but also check whether a proposed "middle" option is actually a disguised decision (e.g. quietly redefining what "correct" infra looks like) rather than a real compromise. He caught me doing this once (suggesting "drop the log bucket requirement from the code" as a safe middle ground for the backend/ reconciliation question when it was actually a policy decision in disguise).

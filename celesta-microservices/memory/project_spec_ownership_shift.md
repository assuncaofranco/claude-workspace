---
name: project_spec_ownership_shift
description: Why devs now own spec + ticket-specific tests at Celesta (the PO only does final cross-ticket integration) — and why that makes the variation matrix mandatory
metadata: 
  node_type: memory
  type: project
  originSessionId: 28e672ea-ad69-45a1-81cb-16985f53b0c3
  modified: 2026-09-21T07:03:30.053Z
---

Stated by Lucas on 2026-09-21, describing how the team's division of work changed.

**What changed.** AI raised the volume of code developers produce. The bottleneck moved downstream: specs (written by the TL at the time) and tests (run by the PO) became the constraint. So developers absorbed both — **devs now own the spec and the ticket-specific tests**. The PO's remaining job is the final integration test *between* tickets.

**The consequence Lucas named himself:** "se a spec está ruim, também é culpa minha. Esse estudo profundo deve ser feito por nós."

**Why it matters operationally:** nothing downstream catches a variant that was never enumerated. Tickets have already been rejected by the PO for partial implementations — correct for the variant we had in mind, silently wrong for the ones nobody listed. There is no safety net below the dev anymore, so the artifact that prevents rejection is the *enumeration*, not the test run.

**How to apply:** this is the reason `ticket-matrix` exists and is mandatory (step 3 of the ticket workflow in `~/.claude/CLAUDE.md`), and the reason step 14 always asks about preprod. Concretely, the division of labour inside that step: Claude enumerates (mechanical, exhaustive, read out of `celesta-constants`/enums/DB — a model doesn't forget the fourth value); Lucas classifies affected/not-affected/equivalent (business judgement, the half that must NOT be accelerated). Every cell cites its source, because a plausible-looking invented matrix is the single most likely way a model reintroduces the exact failure the step exists to prevent.

Related: [[preferences]], [[feedback_review_product_impact_not_just_current_code]].

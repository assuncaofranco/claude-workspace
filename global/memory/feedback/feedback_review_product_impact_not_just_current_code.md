---
name: feedback_review_product_impact_not_just_current_code
description: "When triaging AI code-review comments, judge by future/product risk, not only whether the current code path breaks today"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b5048b97-3031-406d-a807-f7a01f2143a2
  modified: 2026-08-24T09:06:25.657Z
---

When deciding whether to accept or dismiss a code-review comment (Copilot or otherwise), "it's a no-op given
today's code" is not sufficient grounds to dismiss it. Check whether the concern becomes real under a
plausible near-future change to the codebase, and weigh the product-facing impact of that scenario, not just
whether it compiles/passes now.

**Why**: caught during [[project_cls1285_cls2391_review_decisions]]. Copilot flagged that
`$bonus->setStatusSetAt($job->getStatusSetAt())` could null-clobber an already-set value, since the job field
is nullable. First pass: dismissed as N/A because nothing else in the codebase writes that field today, so
there's nothing to clobber. User pushed back: the actual ticket text already hinted the field would eventually
be populated for other transitions too — so the real question is what happens once that lands, not just
whether today's diff is safe in isolation. Once framed that way, the guard is cheap, currently-harmless
insurance against a real future silent-data-loss bug (a stale queue replay erasing a value the app itself had
correctly set) — worth applying even though it changes nothing about current behavior.

**How to apply**: for each review comment, ask "does the codebase's own stated direction (the ticket, the
adjacent specs, an obvious next step) make this scenario likely later, even if it's impossible today?" If yes,
and the fix is cheap/harmless now, lean toward applying it rather than dismissing on "doesn't break today"
grounds alone.

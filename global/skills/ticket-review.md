---
description: Review a ticket's implementation, after ticket-understand has established what it was supposed to do.
argument-hint: <TICKET or branch/PR>
---

# ticket-review

Reviews `$ARGUMENTS`, after `ticket-understand` has established the business intent and current logic. Don't review code cold, against the diff alone — you need the same "what was this supposed to change" context a review needs to be worth anything.

## Steps
1. Read the ticket's spec and plan where the project's SDD keeps them (overlay — at Celesta, the parent's description and the sub-task's) to understand original intent before touching any code. A `_specs/`/`_plans/` file in the repo is legacy, not the source.
2. Check out or read the branch/PR being reviewed.
3. Verify the implementation matches the spec and plan — flag any divergence *before* evaluating code quality. A correct-looking implementation of the wrong thing is still wrong.
4. **Check the variation matrix cell by cell** (`ticket-matrix`: `matrix.md` in the ticket's folder; its criteria are in the spec. On someone else's ticket there is no `matrix.md`: the spec's criteria are what exists). Read the existing matrix — do not rebuild it, and do not accept the implementation as evidence of what it should cover. For each cell: an **A** cell needs a code path and a collection run; an **E** cell's cited shared method must actually be shared in the code as it now stands (a ticket that introduced a branch there silently broke the equivalence, and that's a real finding); an **N** cell's excluding branch must still exclude it. A ticket with no matrix is a finding in itself — say so before reviewing anything else.
5. Evaluate against `shared/coding-standards.md` (canonical for forbidden functions/phpinsights — code should already comply, `ticket-code` applies it at generation time, not just here).
6. Give specific, actionable feedback with file and line references.
7. **When the ticket touches 2+ microservices**, verify across all of them — request payload, responses, normalizers — from the projects root folder so every service is visible at once, not one repo at a time.
8. **Check the API docs match reality** — see `ticket-postman` steps 6-7 (regenerate the spec, compare it against the real response bodies, diagnose with the Form/investigate hierarchy). Don't re-derive that here. A field the endpoint returns but the spec doesn't publish — or the reverse — is a real finding, and reading the diff alone will never surface it.
9. **If this review (human or Copilot) catches something not already in `shared/coding-standards.md`**, add a one-line bullet to its "Lessons from review" section before closing out — that's how the list stays useful instead of the same mistake recurring next ticket.
10. **If the review found a variant the matrix didn't have**, add it to the matrix and record why the enumeration missed it — wrong source, or a dimension never identified. Same loop as "Lessons from review", for coverage instead of style.

## Next
This is the last step for a review-only request. For a full feature/fix cycle, this closes it out after `ticket-code`.

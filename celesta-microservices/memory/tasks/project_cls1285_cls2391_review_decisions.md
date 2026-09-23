---
name: project_cls1285_cls2391_review_decisions
description: "CLS-1285-CLS-2391 (status_set_at fix) — pending PR review decisions across job-library, wallet, promotion"
metadata: 
  node_type: memory
  type: project
  originSessionId: b5048b97-3031-406d-a807-f7a01f2143a2
  modified: 2026-08-24T09:18:39.675Z
---

See [[project_cls1285_cls2391_status_set_at_fix]] for the durable technical findings from this ticket
(listener-ordering pattern, composer dev-branch pattern). This file is the current pending-action status
instead.

Ticket: promotion's `Bonus.status_set_at` was never populated. Fix carries wallet's `BonusSubBalance.statusSetAt`
across 3 jobs (`BonusBalanceDepletedJob`, `BonusRollbackJob`, `BonusBalanceRestoredJob`) to promotion's 3
matching MessageHandlers. Also fixed a real listener-ordering bug in wallet (`BonusPlayedListener`/
`BonusPlayedFreeRoundsListener` now have explicit `priority: 10` on their `postFlush` tag, so their nested
flush — which stamps `statusSetAt` via `BonusSubBalance`'s own `#[ORM\PreUpdate]` — always runs before
`RewardAssetPlayedListener`/`RewardAssetPlayedFreeRoundsListener` read it). Commits: job-library `0503873`
(+ `66f7d37` for the two missing job serialize/deserialize tests), wallet `7590b7c9b` + `75e2093e8`, promotion
`35a446417` + `8b63daf87`.

## DONE — Copilot's null-guard on the 3 promotion handlers (agreed, applied in `d802a88d7`)

`BonusBalanceDepletedJobHandler`, `BonusBalanceRestoredJobHandler`, `BonusRollbackJobHandler` currently do
`$bonus->setStatusSetAt($job->getStatusSetAt())` unconditionally. Copilot flagged: `getStatusSetAt()` is
nullable (in-flight pre-field messages), so this can overwrite an already-set value with NULL.

**Initially dismissed as N/A** (correct for *today's* code: nothing else in promotion writes `status_set_at`,
so there's nothing to clobber — null over null, `[[project_bonus_model_field_removal_risk]]`-style "does it
break today" framing). **User corrected this to a product-risk framing**: the real question isn't "does this
break today," it's "what happens once Promotion *does* write `status_set_at` on its own" — which is plausible
future work, since the original ticket explicitly said "não é só o PLAYED que está sem isso" (CLAIMED/EXPIRED/
CANCELED are out of scope *for this ticket* only). If that ever ships, a stale/replayed wallet message with a
null `statusSetAt` would silently erase a value Promotion itself had correctly set — no error, no log. Product
impact: `status_set_at` already drives the default sort on the Backoffice Player > Bonuses tab, so the bonus
would silently lose its "Updated At" and sink in the list — worse than never having tracked it, because it
looks like clean empty data instead of a data-loss event.

Applied `if ($statusSetAt !== null) { $bonus->setStatusSetAt($statusSetAt); }` in all 3 handlers, plus one new
test per handler asserting `setStatusSetAt` is never called when the job carries null. Also had to
`composer install` after this: `vendor/lancasters/job-library` had been silently reverted to the tagged
`v3.121` by another session/terminal switching this same shared working directory to an unrelated branch
(`CLS-1746-CLS-2008`) — `vendor/` isn't git-tracked, so a branch switch alone doesn't restore it; a plain
`composer install` against the still-correct `composer.lock` fixed it. Worth remembering as a general hazard
in this shared-directory setup: after any branch switch on a repo someone else may have touched, verify
`vendor/` actually matches `composer.lock` before trusting the container's behavior.

## composer.json — dev-branch dependency (intentional, not a bug)

Both wallet and promotion currently require `lancasters/job-library: dev-CLS-1285-CLS-2391` instead of a
tagged release. Copilot flagged this (correctly, in principle) both times. **User's call: leave as-is until
the ticket is approved by the PO — do not switch to a tagged release before that.** Once approved: cut a new
job-library tag from the merged PR, bump wallet/promotion's constraint to that tag, drop the dev dependency.

## Related durable lesson

See [[feedback_review_product_impact_not_just_current_code]] — the general principle behind the correction
above, worth applying to future PR-comment triage, not just this ticket.

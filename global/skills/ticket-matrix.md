---
description: Enumerate every variant a ticket's behaviour can branch on, classify each one, and turn the affected ones into the ticket's acceptance criteria — before any code is written.
argument-hint: <TICKET>
---

# ticket-matrix

Runs after `ticket-understand` and after the ticket's code has been read, before the project's spec phase. Produces one artifact: the **variation matrix** and the acceptance criteria derived from it.

## Why this step exists

Tickets have been rejected by the PO for partial implementations — correct for the variant we had in mind, silently wrong for the three we never listed.

The reason it keeps happening is structural, not careless. Devs now own the spec and the ticket-specific tests; the PO only runs the final integration between tickets. **Nothing downstream will catch a variant that was never enumerated.** A test only finds what someone remembered to test, so the artifact that prevents rejection is the enumeration, not the test run.

Second consequence: once Lucas signs off on the classification, a variant outside the matrix is not a rejection — it's a new ticket. The matrix is the accountability record.

## Division of labour — hard rule

- **Claude enumerates.** Mechanical, exhaustive, read out of the code. This is the half a model is actually better at: it doesn't forget the fourth value.
- **Lucas classifies.** Affected / not affected / equivalent is business judgement, and it's the half that must not be accelerated.
- **Every cell cites its source.** A matrix invented from the ticket description, with plausible-looking values, is the exact failure this skill exists to prevent — and it's the most likely thing to come out of a model. No citation → the cell doesn't exist.

## Steps

1. **Identify the dimensions.** A dimension is anything the ticket's code path can branch on: type enum, model, offering method, claiming event, currency, player state, domain/brand, provider or gateway, feature flag, channel. Take them from the branches in the code you just read — `if`/`match`/`switch`, strategy resolution, form validation groups — not from the description.

2. **Enumerate each dimension's values from an authoritative source**, in this order of preference:
   - a class/const array in `celesta-constants` (e.g. `GameGatewayConstants::FREE_ROUNDS_TYPES`),
   - a PHP enum, a Doctrine column definition, or a validation `choices` constraint,
   - `SELECT DISTINCT` via `db-query` — last resort, and label it as such: it shows what exists in the dev DB, not what is possible.

   Record the source next to the dimension. Never hand-write a list from memory or from a previous ticket's matrix.

3. **Cross-product, then reduce.** Don't try to run the cross product — classify it. Every cell gets one of:
   - **A — affected.** The ticket changes behaviour here. Must be exercised.
   - **N — not affected.** The ticket's code path is never reached. State which branch excludes it.
   - **E — equivalent to `<cell>`.** Same code path as a cell already marked A. Cite the shared method and line (`RewardHandler::handle():112`). "They look the same" is not a justification.

   Reduction methods, applied in this order: equivalence partitioning inside each dimension; boundary values for anything numeric or date-based (0, 1, max, the expiry instant); pairwise (all-pairs) once there are 3+ dimensions and the cross product passes ~20 cells.

4. **Write the acceptance criteria from the A-cells.** One criterion per A-cell, or per group of A-cells sharing an expected outcome. Form: *given `<cell>`, when `<action through BO/Gateway>`, then `<observable result>`.*

   Observable means the collection can read it back. "The bonus is created correctly" is not a criterion. "`GET /player/{id}/bonus` returns a `sub_balance` with `amount = 50` and `status = ACTIVE`" is.

5. **Split it in two.** The criteria from step 4 go into the spec's acceptance criteria, through the project's spec phase, as plain criteria: no table, no A/N/E, no word "matrix" (`rules/writing.md`, "O nosso fluxo não aparece no artefato do time"). The plan phase reads the spec, not this chat, so without them there the plan covers only what someone remembered. The two tables themselves, with classes and justifications, go to `matrix.md` in the ticket's folder (overlay): they are our working record, read again at review and at preprod. When the spec lives in a tracker that re-renders markdown (Jira's ADF), re-read it after the write.

6. **Get Lucas's sign-off on the classification before any code.** Present the N and E cells with their justifications explicitly; those are the ones that carry the risk, and they're the ones he can overrule from product knowledge you don't have.

## Output format

Two tables in `matrix.md` in the ticket's folder. The spec gets only the last column, as plain criteria.

**Dimensions**

| Dimension | Values | Source |
|---|---|---|
| Promotion type | bonus, free_round, cashback | `celesta-constants` `PromotionTypeConstants::TYPES` |

**Cases**

| # | Cell | Class | Justification | Acceptance criterion |
|---|---|---|---|---|
| 1 | free_round × manual × EUR | A | — | given …, when …, then … |
| 2 | free_round × automatic × EUR | E → 1 | same `RewardHandler::handle():112`, offeringMethod only gates segment resolution upstream | — |

A dimension with a single possible value is not a dimension — drop it.

## Downstream — the matrix is consumed, not filed

- `ticket-postman` — one run per A-cell. The collection's iterations *are* the matrix rows.
- `ticket-code` — an A-cell with no code path is an unimplemented requirement, not an edge case.
- `ticket-review` — verify every A-cell is actually covered by the implementation and by the collection.
- `preprod-test` — the preprod run executes A-cells only, and invents nothing new.

## Re-run it when

- the ticket's scope changes — re-enumerate, don't patch it mentally;
- a new value lands in a dimension's source constant mid-ticket;
- review or preprod finds a case the matrix didn't have. Add it, and record **why the enumeration missed it** — wrong source, or an unidentified dimension. That note is the only thing that makes the next matrix better.

## Next
The project's spec, split and plan phases, then `db-query` and `ticket-postman`. The plan's testing strategy must describe each A-cell check (request and expected result), or the implementation's test loop never runs them. It describes them; it never names the collection.

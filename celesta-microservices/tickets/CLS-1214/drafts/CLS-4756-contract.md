# CLS-4756 (celesta-backoffice) — draft contract, NOT approved yet

Assumes the recommended answers to the backoffice plan's open questions (all pending with the user).

Endpoint the front already calls: `POST /api/gateway/domain/{domainId}/finance/transaction_reports`
(`TransactionReportController::getTransactionReportsAction`), JSON array of `TransactionReportResponse`, each element
built by `TransactionReportNormalizer::normalize()`.

New top-level field on each element, next to `withdrawRequestId`:
- name `withdrawRequestIds`, type `integer[] | null` (OpenAPI array of integer, nullable)
- source: statistics `withdraw_request_ids`, passed through unchanged, read with `?? null`

| Line | `withdrawRequestId` (unchanged) | `withdrawRequestIds` (new) |
|---|---|---|
| withdraw, combined payout | lead, e.g. 4290150 | [4290150, 4292746, 4301966] (ascending, lead included) |
| withdraw, single payout or synced before the change | 557795 | [557795] |
| withdraw with no request ID | null | null |
| any other type (deposit*, refund, adjustment) | null | null |
| statistics without the key (not deployed / rolled back) | as today | null |

- A non-null list always has at least one ID; the front can render it with no special case for one ID.
- No new filter/sort/count field.
- The front today reads `movement.withdrawRequestId` in `TransactionReportListItem.js` and `SidePanelInfoCards.js`
  (guarded with `movement.withdrawRequestId &&`).
- CLS-4758 (later, after the front uses the list) removes: the `withdrawRequestId` key from
  `TransactionReportNormalizer::normalize()`, its `OA\Property` in the `TransactionReportResponse` schema, and the
  `withdrawRequestId` expectations in `TransactionReportControllerTest` (and normalizer tests). `withdrawRequestIds`
  stays. Statistics keeps `withdraw_request_id`.
- CLS-4756 also adds a Proteus list scenario in `celesta-qaa-proteus` `transactionReport.pcb-26` asserting both
  `withdrawRequestId` and `withdrawRequestIds`, plus a `TransactionReportApiResponse` type with both fields; the
  celesta-qaa-mock statistics template gains `withdraw_request_ids`.

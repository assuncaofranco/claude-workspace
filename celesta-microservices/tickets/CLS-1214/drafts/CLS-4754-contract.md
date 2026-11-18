# CLS-4754 (celesta-statistics) — draft contract, NOT approved yet

Assumes the recommended answers to the statistics plan's open questions (all pending with the user).

Backoffice reads report lines from statistics `GET /api/bi/transaction_movement` (backoffice
`StatisticsClient::getTransactionMovements()` → `TransactionReportNormalizer::normalize()` maps each element).
Each element is `TransactionMovement::jsonSerialize()`, snake_case keys. Statistics adds ONE key to every element:

| Movement | `withdraw_request_ids` (list<int> or null) |
|---|---|
| `type` withdraw, combined payout | every request ID, ascending, lead included, e.g. [4290150, 4292746, 4301966] |
| `type` withdraw, single payout or synced before the change | [withdraw_request_id], e.g. [557795] |
| `type` withdraw with no request ID | null |
| every other type (deposit*, refund, adjustment, withdraw_request, initial_balance) | null |

- `withdraw_request_id` unchanged (int or null, the lead request).
- No new filter/sort/aggregate field. No backfill (fallback applied on read).
- Backoffice should read the key with a `?? null` default so a statistics rollback does not break the line.
- Statistics OpenAPI schema property name: `withdrawRequestIds` (that schema is camelCase while the payload is snake_case; pre-existing mismatch).
- The statistics mock used by backoffice Proteus suites (`celesta-qaa-proteus` `src/data-services/celesta-statistics/payloads/mockAPI/transactionMovement.ts`) is to be updated by the backoffice sub-task (CLS-4756), whose tests read it.
- Upstream payment (CLS-4753): combined payouts carry `withdrawRequestIds` (JSON int array, ascending, lead included, max 10); lead stays `withdrawRequestId`.
- Sibling CLS-4758 (later) removes the single request ID from the backoffice report line; statistics keeps `withdraw_request_id`.

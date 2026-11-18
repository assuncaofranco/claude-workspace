# CLS-4753 (celesta-payment) — draft contract, NOT approved yet

Assumes the recommended answers to the payment plan's open questions (all still pending with the user).

- Request (`POST /domain/{domainId}/payment-configuration/{id}/payout`): new optional `additionalData.withdrawRequestIds`,
  array of positive integers, unique, max 10 entries (`WithdrawRequestConstants::COMBINED_PAYOUT_MAX_REQUESTS = 10`,
  proposed in `lancasters/constants`, constants sub-task not split yet, pin alias would be `as 1.368`).
  When sent, `additionalData.withdrawRequestId` is required and must be one of its entries (the lead). The lead stays
  `withdrawRequestId`, unchanged (string). A single-request payout sends no list. A one-entry list equal to the lead
  behaves as a single payout.
- Stored (what statistics reads): statistics reads the payment database directly, not an event.
  `TransactionMovementManager::getWithdrawTransactionMovements()` (statistics) left-joins `transaction_additional_data`
  on key `withdrawRequestId`. New row: `additional_data_key = 'withdrawRequestIds'`, `additional_data_value` = JSON
  array of integers ascending, no spaces, e.g. `[4290150,4292746,4301966]`. Row exists only on combined payouts.
  Fallback: existing `withdrawRequestId` row, the lead, as a string (`'4290150'`). Column is VARCHAR(512).
- Jobs (what wallet reads back): in `TransactionCreateJob` / `TransactionUpdateJob`, `additionalData['withdrawRequestIds']`
  is that same JSON string (json_decode it), like `bonusIds` and `bank` today. `additionalData['withdrawRequestId']`
  stays the lead string. `TransactionJobNormalizer` unchanged.
- 409 when any ID in lead + list already has a pending or successful payout for the player, or a lock for any of those
  IDs is held. Body unchanged: `{"errors":["Withdraw request already has a payout"]}`. 400 when lead missing / not in
  list, duplicates, > 10 entries, entry <= 0.
- Payment sorts the list ascending before storing and describing.
- Bank description (Genome `transfer_description`, My.Tu `msg`): IDs ascending joined by ", ", e.g.
  `4290150, 4292746, 4301966`. No list: the lead ID, as today.
- List is provider-agnostic in payment; the wallet decides what is grouped.
- Deploy order: payment first. Older payment (`PayoutType` with `allow_extra_fields`) silently drops an unknown field,
  so a list sent to an older payment pays the total under the lead ID only. Wallet must not send lists until payment
  is fully rolled out.

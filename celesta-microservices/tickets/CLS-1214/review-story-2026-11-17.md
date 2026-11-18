# CLS-1214 — review da story inteira (agente sem contexto, 2026-11-17)

Somente leitura, do git e dos PRs. Opus. Achados verificados em código ou texto, salvo "unverified".

I found no blocking defect. The field contracts line up across all five PRs. The real risks are one path that leaves group members in `processing` forever, and a release manifest that says nothing about rollback or about how long auto payouts are switched off. Every claim below was checked in code on the branches, in celesta-argocd(-parameters) and celesta-sb-argocd, or in the PR text, unless marked "unverified".

## Findings

| Sev | Where | What's wrong | Failure scenario | PR |
|---|---|---|---|---|
| should-fix | wallet `PayoutProcessor.php:226` (409 branch) | When payment answers 409, every member of the group stays in `processing` with `queued=false`. A 409 means only one member already has a payout, so the others have none. | Member B already has a `pending`/`success` payout in payment (for example after an earlier payment 500 that still created it, or a payout that went `timeout` and then `success`). The group {A,B,C} gets 409. B is settled by its old payout. A and C are never sent, never retried, never move to `error`, and the only trace is a warning log. The player's money for A and C is held with no alert. `testGroupPayoutConflictLeavesEveryMemberInProcessing` pins this behaviour. The PR comment "409 … settles from the job as it does today" is wrong for groups. | wallet #1971 |
| should-fix | `releases/CLS-1214.yaml` (whole file) | The manifest has no rollback rules, and the deployer only reads the manifest and the DI. | (a) Payment is rolled back below #1435 after group 5: the list is dropped silently and the total is paid under the lead only. Members are never settled, and the guard no longer sees them. (b) Wallet is rolled back after group 5: old code pays a queued lead's own amount only and settles only the lead. Members stay in `processing`, and `down()` drops `payout_group_id`, losing the record of which requests were in each payout. The safe procedure (pull the crontab line again, wait until no `processing` request has a `payout_group_id`, then roll back; never roll payment back below #1435) is only in the plans' Edge Cases. | manifest (CLS-4755 / 4753 release) |
| should-fix | manifest group 3 | The step does not say that removing the line stops every automatic payout, for all payout methods, until group 5. `PayoutDelayCommand` handles every method, not only Bank Transfer (auto). It also doesn't mention that on prod-2 the suspended `wallet-payout-delay` CronJob is kept as a template for the manual Jenkins job (`kubectl create job --from=cronjob/...`). | Operators see validated requests stop moving to processing on every method for as long as the wallet rollout takes. On prod-2, someone running the Jenkins job in that window runs the command on whatever image is live, which defeats the step. | manifest |
| should-fix (unverified) | payment `TransactionDataHelpersTrait.php:92` | The description is the IDs joined by `", "` with no length cap. Payment only caps the stored JSON at 512 characters, which is about 60 IDs. I found no Genome or My.Tu description limit in the code. SEPA remittance text is usually 140 characters. | With 16 or more seven-digit IDs the description goes past 140 characters. If the bank truncates it, the payout description criterion fails silently. If the bank rejects it, the whole group goes to `error`, gets re-validated, is regrouped the same way and fails again. | payment #1435 |
| nit | wallet `.sdd/_plans/CLS-4755.md:108` | The precedents table says the new column is added "INPLACE". The design section of the same plan and `Version20261116120000` use `ALGORITHM=INSTANT`. | A reader of the plan expects a table rebuild that does not happen. | wallet #1971 |
| nit | wallet `PaymentTransactionJobHandler.php:154` | The group id is the lowest request id, so it is the same every time the same requests are regrouped. The new guard therefore can't tell an old payout's late final job from the current one. | Group {A,B} fails, is re-validated and regrouped (lead A again), and a new payout is pending. A redelivered `failure` job from the old payout moves A and B to `error`. The new payout's `success` then can't move them to `paid`, because `paid` is only reachable from `processing`. The single-request path already has this race; checking the member's `payment_transaction_id` against the job would close it. | wallet #1971 |
| nit | wallet `PayoutDelayCommand::buildPayoutUnits` | Group size is not capped on the wallet side. | A group too long for payment's column gets a 400 and all members go to `error`. Once re-validated it is regrouped the same way and fails again, so it can only be paid one request at a time through the manual PATCH. | wallet #1971 |
| nit | manifest group 5 | "Put the line back" asks the operator to retype a line that differs per environment. prod-1 is `* * * * * … & sleep 30; … & wait`; the others are `*/5 5-18 * * 1-5`. | The operator retypes the wrong schedule. "Revert the group-3 commit" avoids it. | manifest |
| nit | statistics migration + `SynchronizeTransactionMovementCommand::PREPARE_SQL` | The sync copies `SELECT *` from a temporary table created `LIKE transaction_movement`. | A sync run that created its temporary table before the ALTER fails once with a column-count mismatch. It recovers on the next run. | statistics #1063 |
| nit (scope) | celesta-etl `payment_transaction` copy | BigQuery `withdraw_request_id` carries only the lead, and neither `withdrawRequestIds` nor `payout_group_id` reaches BI. | The story's metrics (payouts per paid request, share combined) can't be read from `payment_transaction`. They depend on wallet withdraw transactions' `payment_transaction_id`; whether ETL copies that field is unverified. | none of the five; follow-up |
| nit (text) | PR comments on payment, statistics, wallet and front | Comments are signed "🛠 **sdd-implement**". | That is the playbook's own format, but it is an emoji signature in team-visible text. No co-author trailers or "generated with" lines appear in any commit across the 5 repos plus the 3 Proteus branches. No plan or PR mentions personal tooling, and no backoffice code comments were added. | — |

Contracts checked with no mismatch:
- **Wallet → payment:** the lead goes as an int and is stored as a string. The list goes as ascending ints, is accepted by `CollectionType<IntegerType>`, sorted and stored as `[a,b,c]`.
- **Payment → wallet jobs:** the stored JSON string goes through the normalizer unchanged, and the wallet decodes it.
- **Statistics:** reads the `withdrawRequestIds` row, re-encodes it as ints, and serves `withdraw_request_ids` with `[lead]` as fallback.
- **Backoffice:** passes it through with `?? null`.
- **Front:** reads only `withdrawRequestIds`. No production file still reads `withdrawRequestId`, so CLS-4758 can remove it safely.
- **Amounts and fees:** summed with `bcadd`; the fee is null when every member's fee is null.
- **Locks:** taken in ascending order, all or nothing.

## Acceptance criteria

- **One payout for the total (same player, currency, Bank Transfer auto):** covered by test on both sides. Wallet: `testGroupsBankTransferAutoRequestsOfOneWalletAndConfiguration`, `testCombinedPayoutLifecycleViaCommand`, `testGroupPayoutSendsTheSummedAmountAndFeeWithEveryRequestId`. Payment: `testCombinedPayoutStoresTheLeadAndTheSortedList`. There is no end-to-end test, because Proteus can't run the command.
- **Description contains all IDs:** covered by `GenomeProviderTest` and `MyTuProviderTest` (including the My.Tu signature). The bank-side length limit is unverified.
- **Different currencies or methods paid separately:** covered by test (`separatePayoutRows` provider).
- **Success → all paid:** covered by test (`PaymentTransactionJobHandlerTest` and Proteus pcw-54).
- **Failure → all error, followed up together:** "all error" is covered by test. "Together" is only by reading: the members share the same error message, but nothing in the backoffice links them. That fits the OUT list (CLS-3446).
- **Report shows all IDs:** covered by a test on each layer (statistics, backoffice, front, Proteus pcst-6). The Proteus test seeds the database directly.
- **Player sees each request with its own amount:** covered by Proteus pcw-54, `WithdrawRequestTest` (the new column is not serialized) and reading.
- **A request alone is paid on its own, as today:** covered by test (`testPaysTheLastPayableMemberAloneWithoutAGroup`, `testSingleRequestPayloadCarriesNoWithdrawRequestIds`).
- **On-hold request never combined:** by reading only. The run picks `status = validated` only. CLS-3445 is still in Backlog, so this holds only if it models "on hold" as a separate status.

## Intermediate deploy states

1. **Payment:** nothing visible. Every payout now runs a second guard query for the player. Rolling back is safe until group 5 and unsafe after it (finding 2).
2. **Statistics:** the instant column add is safe; the old backoffice ignores the new key, so the report is unchanged. Rolling back drops the column. Payouts synced while it is gone keep only `[lead]` until they are re-synced.
3. **Crontab line removed:** works on all six environments (supercronic `-inotify`, directory-mounted ConfigMap, prod-2 included). All automatic payouts pause and requests stay `validated` (finding 3). Undo by putting the line back.
4. **Wallet deployed:** the instant migration is safe. Already-queued single PayoutJobs are paid as today. Rolling back is safe while no groups exist.
5. **Crontab line restored:** combined payouts start. Until groups 6 and 7, Finance sees a payout line with the total amount and only the lead's ID. Rolling the wallet back now strands members (finding 2).
6. **Backoffice:** `withdrawRequestIds` is served, and the old front ignores it. A backoffice rollback after group 7 makes every payout line show "-", because the front has no fallback by design.
7. **Front:** shows every ID, one link each. Rolling it back returns to the lead-only link.

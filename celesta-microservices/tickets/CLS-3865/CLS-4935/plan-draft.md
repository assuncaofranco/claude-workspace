# CLS-4935 — {A} [constants] Gift `completed` status and `claimed → completed` transition

Sub-task: https://celesta.atlassian.net/browse/CLS-4935 · Parent: https://celesta.atlassian.net/browse/CLS-3865 · Repository: celesta-constants

## Overview

`Lancaster\Constants\Promotion\GiftConstants` on `master` holds a single status, `STATUS_CLAIMED`. Branch `CLS-4434` (PR #629, open) adds `STATUS_CANCELED`, `STATUS_INITIAL = STATUS_CLAIMED` and `STATUS_TRANSITIONS` with one transition, `canceled` from `claimed`. celesta-promotion feeds these three constants into its `gift_status_workflow` state machine (`config/packages/framework.yaml`: `places`, `initial_marking`, `transitions`), so the transition map is what decides which status changes the API accepts.

This adds the final status `completed`, reachable only from `claimed`, so celesta-promotion can complete a claimed gift through the same state machine once it requires this change ([CLS-4941](https://celesta.atlassian.net/browse/CLS-4941)). The change sits on top of `CLS-4434`, which edits the same file and is not on `master` yet.

## Architecture & Design

- **Base.** The branch `CLS-4935` is created from `origin/master` and merges `origin/CLS-4434` before any change, because `STATUS_INITIAL` and `STATUS_TRANSITIONS` only exist there. The merge is clean today (one file, additions only). If `CLS-4434` is already in `origin/master` when the implementation starts, the merge is skipped.
- **Shape.** The new transition mirrors the `canceled` entry `CLS-4434` adds, and `BonusConstants::STATUS_TRANSITIONS`: keyed by the target status, `'from'` a list, `'to'` the target. Symfony's workflow component reads exactly these keys.
- **Final status.** `completed` is final because no transition lists it in `'from'`. No extra flag or constant expresses finality; the state machine has no way out of a place no transition leaves.
- **Cancel unchanged.** The `canceled` transition keeps `'from' => [STATUS_CLAIMED]`, so canceling a completed gift is rejected by the existing map with no new code.
- **No other status.** `offered` is not added: it does not exist in the backend (see Decisions).
- celesta-backoffice exposes `GiftConstants::STATUSES` through its constants endpoint (`ConstantManager`, `giftConstants.statuses`) and its test compares against the constant, not a literal; it picks `completed` up when it bumps the library. No change there is required by this sub-task.

## Implementation Tasks

1. Create branch `CLS-4935` from `origin/master` and merge `origin/CLS-4434` into it, with the commit message `CLS-4935 Merge branch 'CLS-4434' into CLS-4935`. Skip this task when `origin/CLS-4434` is already contained in `origin/master` (`git merge-base --is-ancestor origin/CLS-4434 origin/master`).
2. In `src/Promotion/GiftConstants.php`, add `const STATUS_COMPLETED = 'completed';` after `STATUS_CANCELED`.
3. In the same file, append `self::STATUS_COMPLETED` to `STATUSES`, after `self::STATUS_CANCELED`.
4. In the same file, add to `STATUS_TRANSITIONS`, after the `self::STATUS_CANCELED` entry, the entry `self::STATUS_COMPLETED => ['from' => [self::STATUS_CLAIMED], 'to' => self::STATUS_COMPLETED]`. Leave `STATUS_INITIAL` and the `canceled` entry as they are.
5. Create `tests/Promotion/GiftConstantsTest.php` (namespace `Tests\Promotion`, extends `PHPUnit\Framework\TestCase`, same style as `tests/Payment/PaymentConfigurationConstantsTest.php`) with:
   - `testCompletedIsAStatus`: `STATUS_COMPLETED` is `'completed'` and is in `STATUSES`.
   - `testCompletedIsReachableOnlyFromClaimed`: `STATUS_TRANSITIONS[STATUS_COMPLETED]` is identical to `['from' => [STATUS_CLAIMED], 'to' => STATUS_COMPLETED]`.
   - `testCompletedIsFinal`: no entry of `STATUS_TRANSITIONS` has `STATUS_COMPLETED` in its `'from'`.
   - `testCanceledIsStillReachableOnlyFromClaimed`: `STATUS_TRANSITIONS[STATUS_CANCELED]['from']` is identical to `[STATUS_CLAIMED]`.
   - `testInitialStatusIsClaimed`: `STATUS_INITIAL` is `STATUS_CLAIMED`.
   - `testEveryTransitionUsesKnownStatuses`: every `'from'` value and every `'to'` of `STATUS_TRANSITIONS` is in `STATUSES`.
6. Run `make test` and confirm the suite passes.

## File Changes

**Modify**
- `src/Promotion/GiftConstants.php` — add `STATUS_COMPLETED`, add it to `STATUSES`, add the `completed` transition to `STATUS_TRANSITIONS`

**Create**
- `tests/Promotion/GiftConstantsTest.php` — the six cases of task 5

The merge of task 1 brings `src/Promotion/GiftConstants.php` as `CLS-4434` leaves it; no other file changes.

## Testing Strategy

- `make test tests/Promotion` for the new class, then `make test` for the whole suite. Both run in Docker; nothing runs on the host.
- `GiftConstants` holds constants only, so the CI 100% coverage gate is unaffected; the test guards the transition map, which is what celesta-promotion's state machine enforces.
- Manual check of the diff against `origin/CLS-4434`: `git diff origin/CLS-4434...CLS-4935 -- src` shows only the three additions of tasks 2 to 4.

## Proteus tests

None in this repository: celesta-constants is a library with no service contract. The transitions are observed through celesta-promotion's gift status endpoint, in [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941)'s plan.

## Edge Cases & Error Handling

- **`CLS-4434` merged to `master` before this branch starts.** Task 1 is skipped; tasks 2 to 6 are unchanged.
- **`CLS-4434` amended after the merge.** Merge `origin/CLS-4434` again before review, with the same message format; the three additions do not touch the lines `CLS-4434` adds.
- **PR diff while `CLS-4434` is open.** The PR against `master` shows `CLS-4434`'s change too until PR #629 is merged; #629 merges first.
- **Complete a completed or canceled gift.** No transition to `completed` leaves `completed` or `canceled`, so celesta-promotion's state machine rejects it.
- **Cancel a completed gift.** The `canceled` transition stays `from` `claimed` only, so it is rejected.
- **Consumers asserting the exact status list.** celesta-backoffice's `ConstantControllerHttpTest` compares against `GiftConstants::STATUSES`, so it follows the constant on the bump.

## Acceptance criteria

- `GiftConstants::STATUSES` contains `claimed`, `canceled` and `completed`, and nothing else.
- `GiftConstants::STATUS_TRANSITIONS['completed']` is `['from' => ['claimed'], 'to' => 'completed']`: a claimed gift can be completed.
- No transition leaves `completed`: completing, canceling or any other transition on a completed gift is rejected.
- No transition into `completed` starts from `canceled`: a canceled gift cannot be completed.
- `GiftConstants::STATUS_TRANSITIONS['canceled']` still has `from` `['claimed']` only.
- `GiftConstants::STATUS_INITIAL` is still `claimed`.

## Dependencies

- Depends on [CLS-4434](https://celesta.atlassian.net/browse/CLS-4434), celesta-constants PR #629 (gift `canceled` status and transitions): this branch merges `origin/CLS-4434` until #629 is on `master`, and #629 merges before this sub-task's PR.
- Blocks [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941), celesta-promotion complete a claimed gift and edit its value: it requires this change from branch `CLS-4935` (`"lancasters/constants": "dev-CLS-4935 as <next version>"`); the repin to the released tag follows once the lead announces it.
- Related to [CLS-4942](https://celesta.atlassian.net/browse/CLS-4942), celesta-backoffice: its constants endpoint exposes `GiftConstants::STATUSES` and gains `completed` on its bump.

## Decisions

- **Which base does this branch start from, given that `CLS-4434` edits the same `GiftConstants.php` and is not on `master`?** — `origin/master` with `origin/CLS-4434` merged in before implementing, while PR #629 is open; the transition map and `STATUS_INITIAL` this sub-task extends only exist there · answered by Lucas Franco, 2026-11-17
- **The parent lists `offered` among the gift status changes. Is `offered` added as a status?** — No. `offered` does not exist in the backend; this plan adds `completed` only · answered by Lucas Franco, 2026-11-17

## Out of Scope

- Merging, tagging and releasing the library: the lead's, once the parent is accepted.
- Accepting `completed` in celesta-promotion's gift status form and endpoint: [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941).

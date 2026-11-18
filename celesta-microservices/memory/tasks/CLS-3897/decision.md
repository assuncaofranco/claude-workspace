---
name: cls3897-tooling-coverage-decision
description: "CLS-3897 — PHP test tooling (test-utilities, clock-mock, fixtures) excluded from the 100% coverage epic CLS-2947; clock-mock archive still pending an org admin"
metadata:
  node_type: memory
  type: project
  originSessionId: c8b315d2-2f7e-49ed-ac0a-2286bb5c7ea1
  modified: 2026-10-26T08:28:59.902Z
---

Decision posted by Lucas as a comment on CLS-2947 on 2026-10-26: all three repos excluded from the epic, no new sub-task.

- `lancasters/clock-mock` is only required by `lancasters/test-utilities`, and test-utilities has no consumer. Checked on 2026-10-23/26: composer.json + composer.lock on the default branch of all 76 celesta-tech repos, plus org code search. Non-default branches were not checked (GitHub only indexes the default branch).
- The `ClockMock` in wallet/payment tests is `Symfony\Bridge\PhpUnit\ClockMock`, not ours: don't confuse them.
- celesta-fixtures is in use. Its only class, `CustomOrderFilesLocator`, is wired in wallet `config/services.yaml` as the Alice locator, so it's covered indirectly by the wallet suite. Wallet coverage excludes vendor, so no figure shows that.

**Why:** Lucas's reading of the epic: the goal is that every line that runs is covered, directly or indirectly. Dead code has no lines to cover.

**How to apply:** pending: archive clock-mock. Lucas is a `member` without admin on the org, so it needs an org admin. The ticket only asks to archive clock-mock; test-utilities is only excluded, not archived, unless Lucas decides otherwise.

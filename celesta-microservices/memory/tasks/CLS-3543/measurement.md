---
name: cls3543-notification-coverage-measurement
description: "CLS-3543 (celesta-notification, Go) — how coverage is measured today, baseline numbers 2026-10-21, and the open decision on what counts"
metadata:
  node_type: memory
  type: project
  originSessionId: 5a3f780c-f88d-4435-a730-3ce580feff04
  modified: 2026-10-22T14:43:17.810Z
---

Sub-task of CLS-2947 (Team D 100% coverage). Jira description empty, `Github repository` field unset on 2026-10-21. CMS sibling CLS-3540 is the plan model; game-go sibling CLS-3539 is PR #112 (open), the Go precedent: `-coverpkg=./internal/...`, gate 100, gomonkey + `-gcflags=all=-l` for "dead code" branches.

**Measuring locally:** `make init` fails without `GITHUB_ACCESS_TOKEN` (private `celesta-go-helper`) → `GITHUB_ACCESS_TOKEN=$(gh auth token) make init`. Then
`docker compose -f docker-compose.dev.yml exec notification.consumer go test -count=1 -coverpkg=./internal/... -coverprofile=./tmp/cov.out ./...` and `go tool cover -func`. Summing the profile by hand needs dedup by block key (coverpkg repeats blocks per test binary).

**CI today:** `tests-go.yml` default flags `-cover -count=1`, no profile, no gate (`ENABLE_COVERAGE_THRESHOLD` unset). Prints only per-package figures; no total.

**Baseline 2026-10-21, master f7fe733:**
- per package, as CI: 25.4%
- `-coverpkg=./...`: 43.8%
- `-coverpkg=./internal/...` (cmd/config out, as parent says): 52.6% = 131/249 statements; biggest holes `domainkafka/admin.go` 0/54, `sender.go` 44/76.

**Decisions 2026-10-22 (Lucas), plan phase:** team resists prod changes → tests first. admin.go untouched except int16 conversion extracted to `(int) (int16, error)` (checks came from gosec, CEL-4732 `66693e1`); Setup covered with `kfake` in-process. kfake pinned `v0.0.0-20250603004440-37eecbb8927f` (= franz-go v1.19.5 tag) — `@latest` bumps prod franz-go 1.19.5→1.22.1 + x/net/crypto, never use it. IAM callback extracted to named func, tested via `t.Setenv` (missing profile / IMDS disabled), proven offline. InitSenders returns error, main does Fatal. No gomonkey in this repo. Delete `internal/utils` + root `internal/messaging` (no importers, grep-checked). Gate 100 in CI same PR; make test/coverage/coverage-html in container with coverpkg. CLAUDE.md and `_plans/CEL-9110.md` out of scope. All test paths prototyped in a throwaway copy in the container.

**Plan written to CLS-3543 description 2026-10-22, label `sdd-plan`.** Next phase: `/sdd-implement CLS-3543`. Unreachable-dial seed is `127.0.0.1:1` (0.3 ms, no DNS); `kafka.invalid` took 174 ms via DNS.

**Implemented 2026-10-22 on branch `CLS-3543`, uncommitted:** 100.0%, lint 0, reviewer No findings after 2 rounds. One deviation from the plan, Lucas's call: `//nolint:funlen` on `main` (InitSenders change took it to 103 > 100 lines) — the plan's acceptance criterion "no production change beyond…" should mention it.

**2026-10-22, closing:** acceptance criteria in Jira updated with the nolint; manual check passed (15 topics created, `cls3543-check-3` landed in `dev-madnix-user`); labels `sdd-plan`+`sdd-implement`. Committed `17bb6b7` and pushed to `origin/CLS-3543` 2026-10-22; PR #171 opened same day.
Local manual-check gotchas: shared local SQS `dev-notification` holds ~310 stale messages from other local runs — run the consumer with `-e SQS_QUEUE_PREFIX=<throwaway>-` on a throwaway queue instead. `NotificationJob` body on the queue is the **flat** notification (no `"notification"` wrapper), attribute `Job-Class-Name`. The consumer panics on the first send error (e.g. topic `player-session`, which `Setup` never creates and the client won't auto-create) — pre-existing, out of scope.

Go counts statements, not lines. **Decided 2026-10-21 (Lucas):** the number is `-coverpkg=./internal/...` statements (third view).

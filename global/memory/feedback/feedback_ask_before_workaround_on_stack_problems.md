---
name: feedback-ask-before-workaround-on-stack-problems
description: "When the local stack misbehaves (container, cache, DB state, service down), report it and let Lucas fix it — never route around it with a workaround"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a6b3439f-08c3-410b-8d8f-9a3dd1ffd60f
  modified: 2026-08-27T07:57:12.060Z
---

When something goes wrong in the local stack — a service not responding, stale Redis cache, purged DB state, container out of sync — stop and tell Lucas so he can fix it. Do not invent a workaround (clearing a cache pool, reloading fixtures, recreating a container, patching env values) to get unblocked.

**Why:** he owns the environment and often already knows the real cause or is mid-repair on it. Silent workarounds mask the actual problem, can destroy state his other sessions depend on, and produce test results that look green for the wrong reason. Said explicitly on 2026-08-27 after I ran `hautelook:fixtures:load` without the project's own `--no-bundles` flag, broke domain-1 resolution in the local Backoffice, and was about to clear the Redis pool instead of reporting it — while he was already reinstalling CRM/memberzone.

**How to apply:** when a stack-level failure blocks verification, say plainly what broke, what I did just before it, and what I think the cause is — then wait. Distinguish this from a *code* defect in the ticket, which I should still investigate and fix myself. Also: before running any project-level setup command (fixtures load, migrations, container recreate), check how the repo's own `install.sh`/`Makefile` invokes it and use the same flags.

Related: [[preferences]]

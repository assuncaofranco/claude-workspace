---
name: project-pc-migration-2026
description: "PC migration in progress (2026-08-09) — staging folder location, restore prompt path, and known gotchas to fix on the new machine"
metadata: 
  node_type: memory
  type: project
  originSessionId: 691d8123-3238-4da9-befd-0b59615b6bab
  modified: 2026-08-11T09:44:11.574Z
---

User is migrating from this computer to a new one. A full audit of local (non-cloud) config/credentials was done and staged into `~/Desktop/migracao-pc-novo/` on the OLD machine, with a `README.md` inside mapping every subfolder to its destination, and a `RESTORE_PROMPT.md` with step-by-step restore instructions for a fresh Claude Code session on the NEW machine.

**Why:** most secrets/logins live in 1Password (cloud), but a lot of local config that *points at* those secrets — ssh config/keys, kube/aws config, Claude Code's own global config+memory, composer auth, editor settings, and a pile of loose note files with plaintext credentials scattered around the home dir — does not sync anywhere and had to be found and copied by hand.

**How to apply:** if you're reading this on the new machine, the migration already happened — see [[reference_pc_migration_gotchas]] for the specific bugs/loose ends that need attention (ssh config path bug, a bastion key that was never found on disk, an MCP server with a hardcoded path). Don't re-derive this from scratch; the folder's README.md and RESTORE_PROMPT.md are the source of truth for what to copy where.

**Status as of 2026-08-11:** verified on the new machine (macOS, `/Users/l.franco`) — ssh keys/config, AWS config/credentials, kube config, k9s config, and Claude Code global config+memory were all actually restored on 2026-08-10. User still has the old machine on hand for ~1 more week (until ~2026-08-18), which is the deadline to pull anything still missing. Remaining open items, all in [[reference_pc_migration_gotchas]]: shell aliases (`.zshrc`) were never in the audited bundle at all — needs manual pickup from old machine; AWS MFA session profile (`celesta-global-mfa`) had expired, which cascades into every EKS kube context's exec-auth and looked like "Lens can't find server configs" — fixed by re-running the `aws-mfa` login, not a file issue; `bastion-celesta-staging` key still unresolved (pre-existing, not new); `mcp-celesta` project + its MCP server entry not yet recreated on the new machine.

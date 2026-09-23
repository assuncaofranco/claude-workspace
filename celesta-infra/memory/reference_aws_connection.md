---
name: reference-aws-connection
description: "How to get a working AWS session on this machine to run terraform/aws cli — profiles, MFA, and the quirks that break it"
metadata: 
  node_type: memory
  type: reference
  modified: 2026-09-09T10:53:06.096Z
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
---

Read this before running any `aws` or `terraform` command against a real Celesta account. General infra facts (repos, accounts, environments) live in [[project_infra_context]] — this file is just the mechanics of getting a valid session, kept separate so reading infra context doesn't burn tokens on connection trivia.

## The one command that matters

```
awsmfa
```

Alias in `~/.zshrc`: `aws-mfa --profile celesta-global`. Prompts Lucas for a 6-digit code from his phone's Google Authenticator (not 1Password — see below). Writes the fresh session **directly into `[celesta-global]`** in `~/.aws/credentials`.

**This requires an interactive human typing a live code — I cannot run it myself.** If any `--profile celesta-global` command fails with an expired-token or credential error, tell Lucas to run `awsmfa` in his own terminal, then retry.

## Why `credential_process` doesn't just work automatically

`~/.aws/config`'s `[profile celesta-global]` has a `credential_process` line pointing at `~/.aws/aws-mfa-op.sh`, currently **commented out**. That script was meant to fetch MFA codes from a 1Password item called "AWS Celesta" — but that item never had a One-Time-Password field configured, on this machine or the old one. This is not a regression, it never worked; the manual `awsmfa` flow (formerly just `mfa` on the old computer) is Lucas's normal way of doing this, not a workaround. Fixing 1Password properly is a known, low-priority TODO for him — don't push it.

## Why the profile name matters more than usual here

`lrgi-terraform`'s `iam/` and `backend/` roots hardcode `profile = "celesta-global"` literally inside `backend.tf` and `main.tf` (via the null-label module's derived value, or a literal string). **Setting `AWS_PROFILE` as an env var does nothing for these** — Terraform reads the profile name from the code, so the named profile itself must hold valid credentials. This is why the session has to land in `[celesta-global]` specifically, not some other name.

Other profiles (`celesta-staging-1`, `celesta-prod-1`, `celesta-preprod`, etc.) assume-role via `source_profile = celesta-global` — fixing `celesta-global`'s session unblocks all of them too.

## Credentials file sections (`~/.aws/credentials`), for orientation

- `[celesta-global]` — the one that matters, written fresh by `awsmfa`.
- `[celesta-global-longterm]` and `[celesta-global-long-term]` — same long-term IAM keys, two spellings. The hyphenated one exists because the classic `aws-mfa` tool's default naming convention expects exactly that spelling; both were populated once and shouldn't need touching again.
- `[celesta-global-mfa]` — legacy, was the old alias's output target before the alias got fixed to write straight to `celesta-global`. No longer used; ignore it.

## If long-term keys ever look genuinely missing

Before assuming they need regenerating, check `~/Desktop/migracao-pc-novo/infra-access/aws/` — a backup brought over from Lucas's previous machine during migration. Contains `credentials`, `credentials.backup`, `config`. Read structure (section names) only, never print key values into chat — these are real secrets.

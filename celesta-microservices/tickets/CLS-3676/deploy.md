# CLS-4053 deploy

- **What:** celesta-promotion only (PR #574). No other service, no shared library, no composer change.
- **Order:** none. The gateway is untouched and keeps mapping the new 409 to 404, so promotion can go alone.
- **Migrations, config, flags:** none.
- **Intermediate state:** none; one service.
- **Rollback:** redeploy the previous promotion image. Nothing to undo in data: the guard only reads.
- **Preprod:** branch deployed to pp1 on 2026-10-27, deposits and claims checked through BO and gateway.

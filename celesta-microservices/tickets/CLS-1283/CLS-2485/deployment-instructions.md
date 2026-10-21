1. Release job-library
2. Deploy sb-argocd (prod-2). Must be before wallet: removes the cronjobs that call the deleted commands
3. Deploy wallet
4. Check in AWS SQS that promotion-bonus.fifo is empty and promotion-failed has no BonusPlayedJob / BonusRollbackJob (discard them if any)
5. Deploy promotion. Must be after wallet: a BonusRollbackJob reaching it without the handler blocks that bonus's FIFO group

Rollback: promotion first, then wallet.

PS, not a dependency of this deploy: the prod-2 Jenkins "run cronjob" list (celesta-jenkins-config) still offers wallet-bonus-model-set-status, wallet-expire-bonus-offer and wallet-expire-bonus-validity, and rundeck octopo* still has scripts calling those commands. A separate DevOps ticket should remove them.

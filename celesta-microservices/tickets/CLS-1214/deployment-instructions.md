# CLS-1214 — instruções de deploy

Escrito em 2026-11-17 nos campos do pai e na seção Post deployment dos 5 PRs (a lista é a mesma). Foi no pai (Deployment instructions e Rollback instructions) e na
seção de post deployment da descrição dos 5 PRs. O campo Deployment instructions já tem a linha do manifesto
(`Release manifest: …`, escrita pelo `sdd-release`): fica, e a lista entra embaixo dela.

Fonte da ordem: `releases/CLS-1214.yaml` (celesta-releases, `main`).

## Deployment instructions (texto)

```
1. Merge celesta-payment#1435
2. Merge celesta-statistics#1063
3. Remove the `withdraw-request:payout-delay` line from the wallet crontab (`<env>/wallet/cronjobs/crontab` in celesta-argocd-parameters, every environment). Until step 5 no payout runs automatically, for any payout method. On prod-2 do not run the Jenkins jobs that run this command either: `celesta/prod-2/wallet/jobs/payout-delay`, and the `wallet-payout-delay` choice of `celesta/prod-2/wallet/jobs/jobs`.
4. Merge celesta-wallet#1971
5. Once every wallet pod runs step 4, revert step 3 (the same file, so each environment gets back its own schedule), and on prod-2 the Jenkins jobs may run again.
6. Merge celesta-backoffice#3339
7. Merge celesta-backoffice-front#2311
```

## Rollback instructions (texto, ordem inversa)

```
1. Revert celesta-backoffice-front#2311
2. Revert celesta-backoffice#3339
3. Remove the `withdraw-request:payout-delay` line from the wallet crontab again (`<env>/wallet/cronjobs/crontab` in celesta-argocd-parameters) and, on prod-2, do not run the Jenkins jobs that run it. Wait until no withdraw request is in `processing` with a `payout_group_id`.
4. Roll back celesta-wallet#1971
5. Revert step 3 of the rollback (the line goes back, the Jenkins jobs may run again)
6. Roll back celesta-statistics#1063
7. Roll back celesta-payment#1435 only after step 4. Never roll it back while the wallet is still sending lists.
```

## Observar depois (não vai no campo; vai na descrição dos PRs só se o Lucas quiser)

- Depois do passo 5: pagamentos de players com muitos pedidos. Uma descrição com mais de uns 16 ids passa de 140
  caracteres e o banco pode truncar ou rejeitar (não verificado). Se o grupo falhar por isso, os pedidos voltam a
  `error` e só saem um a um pelo PATCH manual.
- Depois do passo 2: a primeira rodada do sync de movimentos pode falhar uma vez com "column count" se a tabela
  temporária foi criada antes do ALTER. Se recupera na rodada seguinte.

## Por que cada passo (do nosso lado, não vai no ticket)

| Passo | Por quê | Fonte |
|---|---|---|
| payment antes de tudo | o payment ignora em silêncio um campo que não conhece (`allow_extra_fields`): uma lista mandada a um payment velho paga o total só sob o lead e os outros pedidos ficam em `processing` | plano do 4753, edge cases; `PayoutType` |
| statistics antes da wallet | a coluna `withdraw_request_ids` precisa existir antes de haver payout combinado; sem ela o movimento só tem o lead até um re-sync manual | plano do 4754 |
| tirar a linha do crontab antes da wallet | um pod velho da wallet pagaria só o valor do lead de um grupo e acertaria só o lead; os membros ficam em `processing` | plano do 4755, rollout |
| a linha é só o crontab | o `payout-delay` roda pelo supercronic do Deployment `wallet-cronjobs`, que recarrega o crontab com `-inotify`, sem reiniciar; o CronJob base é apagado nos overlays do celesta-argocd e suspenso no prod-2 (celesta-sb-argocd) | `celesta-argocd/microservices/wallet/kustomize/overlays/*/cronjobs`, `celesta-sb-argocd/.../prod-2/cronjobs/patch_suspend_cronjobs.yaml`, `celesta-argocd-parameters/<env>/wallet/cronjobs/crontab` |
| Jenkins no prod-2 | o job `payout-delay` e a opção `wallet-payout-delay` do job `jobs` rodam o command no pod ativo, sem a linha do crontab: rodar um deles no meio anula o passo 3. Nenhum dos dois tem agendamento: só rodam se alguém disparar | `celesta-jenkins-config/config/celesta/prod-2/wallet.yaml`, `celesta-wallet/ops/jenkins/wallet-payout-delay.jenkinsfile` |
| "reverter o passo 3" | a linha muda por ambiente (prod-1 roda duas vezes por minuto, os outros a cada 5 min em dias úteis); reverter o commit devolve a de cada um | `celesta-argocd-parameters/<env>/wallet/cronjobs/crontab` |
| backoffice depois da wallet | até o backoffice subir o relatório mostra o payout combinado com o valor total e só o id do lead; o front antigo ignora a chave nova | plano do 4756 e do 4757 |
| front por último | o front só lê `withdrawRequestIds`; com um backoffice sem a chave a linha mostra `-` | plano do 4757, decisão "sem fallback" |
| rollback do payment só depois da wallet | com o payment abaixo do #1435 a lista é descartada, o total vai sob o lead e os outros membros nunca são acertados | plano do 4753 |
| esperar não haver `processing` com `payout_group_id` antes de voltar a wallet | o `down()` apaga a coluna `payout_group_id`: sem ela se perde o registro de quais pedidos estavam em cada payout | `Version20261116120000` (wallet) |
| statistics rollback | o `down()` apaga a coluna; movimentos sincronizados enquanto ela não existe ficam só com o `[lead]` até serem sincronizados de novo | `Version20261408000001` (statistics) |

Migrations: statistics e wallet são colunas nullable adicionadas por `INSTANT` no `up()` (a wallet na tabela e na
audit), sem lock. Nenhuma roda por comando manual; o deploy as roda.

## CLS-4758 (2026-11-17)

Entrou como passo 8 do deploy ("Merge celesta-backoffice#3341, once step 7 is in production") e como primeira linha
do rollback (`Revert celesta-backoffice#3341`), com os números seguintes deslocados em um. O #3341 contém os
commits do 4756 por merge: o #3339 vai antes, senão o código do 4756 entra no master por um PR revisado só pela
remoção.

## Pendente (anterior ao 4758)

- CLS-4758 (backoffice, tira o `withdrawRequestId`): quando for planejado, entra como passo depois do front em
  produção, e o rollback ganha a linha dele no começo.
- Manifesto: os passos manuais 3 e 5 do `releases/CLS-1214.yaml` ainda dizem "put the line back" e não dizem que a
  retirada pausa todos os métodos nem citam o Jenkins do prod-2. Reescrever com o `sdd-release` (numa execução do
  4755) depois que o texto acima for aprovado.
- Escrever: campos do pai, descrição dos 5 PRs.

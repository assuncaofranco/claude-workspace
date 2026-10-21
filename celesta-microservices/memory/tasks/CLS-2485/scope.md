---
name: cls2485-scope
description: "CLS-1283-CLS-2485 (MoveBonusCleanup, remove jobs and handlers) — escopo fechado em 2026-10-14 com evidência de produto, código, argocd e APM; o que entra, o que fica e por quê"
metadata:
  node_type: memory
  type: project
  originSessionId: d4d41c83-3dfa-480f-b425-829f01c2eb7a
  modified: 2026-10-20T15:35:28.315Z
---

Ticket nosso: **CLS-2485**, subtask do CLS-1283 (épico CLS-1277). Sem descrição; escopo definido por nós.
"Jobs" = **todos**: messenger jobs, handlers e console commands do bônus legado da wallet.

**Sobreposição com o CLS-1624:** a branch `CLS-1283-CLS-1624` (Socrates, jul/2026) já removia os jobs de
status, apesar do título "controllers, entities, form types". Socrates fechou os PRs; Rasoul (dono atual)
disse que não remove. Ficou conosco (Lucas, 2026-10-14). O spec dessa branch é bom ponto de partida.

## Entra

| Item | Repo | Evidência |
|---|---|---|
| dispatch de `BonusRollbackJob` em `TransactionRollbackListener` + routing | wallet | duplicata: o mesmo flush PLAYED→CLAIMED já emite `BonusBalanceRestoredJob` via `RewardAssetClaimedListener` |
| `BonusRollbackJobHandler`, `BonusPlayedJobHandler` | promotion | Played sem produtor; Rollback morre com o dispatch |
| `BonusPlayedJob`, `BonusRollbackJob`, `BonusClaimedJob` | job-library | Claimed sem produtor nem consumidor |
| `expire:bonus:offer`, `expire:bonus:validity`, `bonus-model:refresh-state` | wallet | no-op com TODO de cleanup; substitutos já rodam na promotion em todo ambiente |
| CronJobs `wallet-bonus-model-set-status`, `wallet-expire-bonus-offer` | `celesta-sb-argocd` (prod-2) | vivos: 9.231 e 3.826 execuções no APM em 30 dias, todas "Skipping" |
| `bonus:cancel` | wallet | muda status de bônus (conceito da promotion) sem avisar a promotion → divergência tipo healthcheck 089; substituto = cancel via BO/promotion → `RefundHandler`; **0 execuções em 30 dias** em todos os envs |
| parâmetro `cronjob` do Jenkins, `ops/scripts/*` | wallet, `celesta-jenkins-config` | só disparo manual |

## Fica

- `transaction:adjust-bonus-balance`: mexe em **sub_balance**, que continua sendo da wallet; integrado ao
  fluxo novo (`BONUS_ADJUSTMENT_DOWN` ∈ `TYPES_BONUS_OUT` → `BonusBalanceDepletedJob`). Raro, não legado.
- rundeck `celesta-ops/.../octopo*`: infra antiga, fora.

## Andamento

- 2026-10-16: PR [celesta-sb-argocd#846](https://github.com/celesta-tech/celesta-sb-argocd/pull/846) aberto (branch `CLS-1283-CLS-2485`), tira os 2 CronJobs + patch do prod-2. Merge exige aprovação de qualquer membro do `team-o` (Lucas não é). App tem `prune: true`.
- Mensagem ao Marcello (voltou de férias) redigida em PT, com links; decisão: a limpeza do argocd fica no nosso ticket.

- 2026-10-16: **modo antigo de SDD** (Lucas: o plugin novo é para os próximos tickets, rodado pelo TL). Spec/plano em arquivo nos repos. PRs abertos: wallet #1911, promotion #558, job-library #541; sb-argocd #846 atualizado com a ordem. jenkins-config: sem push, pedido ao team-o no #846 (patch local na branch `CLS-1283-CLS-2485`).
- Decisão revista pelo Lucas: wallet e promotion **usam `dev-CLS-1283-CLS-2485`** da job-library na review (commits 037176ba9 / ca9d75338) e trocam para a tag antes do merge. jenkins-config sai dos PRs: vai no DI, o Marcello abre ticket para o DevOps.
- Achado de deploy: `promotion_bonus_sqs` tem `max_retries: 9999` e é FIFO por bonusId, então `BonusRollbackJob` sem handler trava o grupo do bônus. Ordem obrigatória. Instruções em `tickets/CLS-1283/CLS-2485/deployment-instructions.md`.
- Teste local: suíte da wallet tem ~338 falhas **pré-existentes** pelo `.env.dev` do Lucas (CRM_HOST/GUARD alterados, mocks de CRM e sensor não batem); comparei lista branch × master, zero falha nova.
- 2026-10-16: Newman local verde, 34 asserções, repetível (`~/.claude/postman/CLS-2485/run.sh`; armadilhas no `CLS-2485.md`: roundId dedup, model direct, GW não lista played, AUTO_INCREMENT da promotion movido para 1000, player 1 com ajuste +200).
- 2026-10-16 review (passo 13): matriz conferida célula a célula, nenhuma variante nova; grep cross-repo zero referências; YAML dos boundary docs ok; nenhum endpoint mudou. Achados: phpinsights `::error` nos 2 arquivos tocados da wallet (hook passa por threshold, regra é 100%) — corrigido e pushado; comentário no teste novo explicando que o transporte só guarda o que o rollback despachou (kernel reboota por request). Lição anotada em `coding-standards.md`.
- 2026-10-19: DI curto (formato do time: lista de ordem, sem número de PR, Jenkins/rundeck como "PS" não-dependência) gravado nos **campos** do CLS-2485, não em comentário (Lucas apagou o comentário): Deployment instructions = `customfield_10122`, Rollback instructions = `customfield_10133`, Release note = `customfield_11637` (só job-library). Decisão: review primeiro, PP depois da aprovação seguindo o DI.
- 2026-10-20: os `_specs`/`_plans` em arquivo saíram dos PRs (wallet `77030cb5e`, promotion `a8e348d8f`,
  job-library `9ba9502`) e das descrições; as cópias estão em `tickets/CLS-1283/CLS-2485/<repo>/`. Regra nova:
  PR oficial só com o que a regra do time pede; o nosso material fica na pasta do ticket.
- Falta: passo 15 (preprod, domínio 216, precisa de aposta SB real), aprovação team-o no #846, e **no fim** fechar o DI com o Lucas. Merge/tag da job-library **não é nosso**; o DI só diz que a tag tem de existir e o composer trocar para ela antes do merge.

## Ordem de deploy

wallet + sb-argocd → drenar `promotion-bonus.fifo` → promotion → job-library com tag nova.

**Why:** a régua que o Lucas fixou: partir da função de produto, achar o substituto, e só então
confirmar desuso em prod (APM, não logs — ver `datadog-reference.md`).

**How to apply:** próximo passo é `ticket-matrix`; spec/split/plano agora são o plugin SDD (Jira).

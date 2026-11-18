# CLS-1214 — passos do SDD

Combinar saques do mesmo player num payout. Story em Split. Todas as sub-tasks são nossas, A-Team,
assignee Lucas (conferido no Jira em 2026-11-13).

Blocks: 4753 → 4754 ∥ 4755; 4754 → 4756 → 4757 → 4758.

Plano roda junto quando um não lê o resultado do outro (lição do CLS-4779). Aqui o contrato nasce em
cadeia: o 4753 define o que o payout carrega, o 4754 o que a statistics grava, o 4756 o que o BO
expõe. Então cada plano espera o push do plano de quem ele lê, e só 4754 ∥ 4755 rodam juntos.

| # | Comando | Lê o plano de | Para em | O que avaliar |
|---|---|---|---|---|
| 1 | `/sdd-plan CLS-4753` | — | rascunho | contrato da lista de ids (4754 e 4755 dependem dele), guarda de duplicidade para todos, descrição Genome e My.Tu |
| 2 | `/sdd-plan CLS-4754` ∥ `/sdd-plan CLS-4755` | 4753 | rascunho | 4754: lista com fallback para o id único, o que o 4756 consome. 4755: agrupamento (player, moeda, método), on hold fora, grupo inteiro paid ou error, grupo de um igual a hoje |
| 3 | `/sdd-plan CLS-4756` | 4754 | rascunho | campo novo no relatório, id único mantido (o cleanup é o 4758) |
| 4 | `/sdd-plan CLS-4757` | 4756 | rascunho | front mostra a lista; linha sem lista (payout antigo) |
| 5 | `/sdd-plan CLS-4758` | 4757 | rascunho | só remove; nada além |
| 6 | `/sdd-implement` na ordem dos Blocks | — | pedido de push | diff × plano, testes, atribuição; depois revisores, CI (`gh workflow run`), `sdd-release`, review sem contexto, To review |

Board: plano no PR → Planned; implement → In Progress, e o pai → Implementing.

## Decisões

| Data | Pergunta | Decisão e motivo | Quem |
|---|---|---|---|
| 2026-11-17 | fechamento dos cinco implements | todos com `sdd-reviewed` e todas as sub-tasks (4753–4757) em To review. Manifesto `releases/CLS-1214.yaml`: 1 payment #1435 · 2 statistics #1063 · 3 manual (tirar a linha `withdraw-request:payout-delay` do crontab da wallet) · 4 wallet #1971 · 5 manual (devolver a linha) · 6 backoffice #3339 · 7 front #2311. PRs do proteus abertos, merge do QA: #822 payment, #827 statistics, #828 wallet. Custos no Jira: 4753 $39.20, 4754 $22.38, 4756 $6.58, 4755 "no mínimo $57.47" (parcial), 4757 sem custo (não separável). 4758 segue adiado até o 4757 em produção. Review da story inteira rodando | Lucas |
| 2026-11-17 | 4758 | sem gates nossos, só os revisores do SDD; plano #3341 e implement na mesma conversa. A branch recebeu merge de `origin/CLS-4756` (`a3d9793da1`, como o 4748 com a CLS-4745) e o plano foi aplicado inteiro em cima: `withdrawRequestId` sai do normalizer, do OpenAPI e dos testes. Revisão em 2 rodadas, dois nits (descrição do `withdrawRequestIds`), CI verde (run 44065462555), manifesto grupo 8 (`db0756f`) depois do front, sem ação manual. PR aberto, sem merge, até o front estar em produção. Merge: #3339 antes do #3341 (o #3341 carrega os commits do 4756 até lá). Sem comentário de custo. Instruções de deploy e rollback do pai e dos 6 PRs ganharam o passo 8 | Lucas |
| 2026-11-17 | review da story inteira (agente sem contexto) | sem bloqueante; contratos batem nos 5 repositórios; achados em `review-story-2026-11-17.md`. Aplicados: 409 de grupo em `critical` com todos os ids e "INPLACE"→"INSTANT" na tabela de precedentes do plano da wallet (emenda + código no #1971); regras de rollback, pausa de todos os métodos, Jenkins do prod-2 e "reverter o passo 3" nas instruções de deploy. Fora: descrição longa demais (só anotada), job final antigo reentregue, sem teto de grupo, ETL do BigQuery (follow-up, avisar o PO), assinatura 🛠 do playbook | Lucas |
| 2026-11-17 | instruções de deploy | escritas no pai (Deployment instructions mantendo a linha do manifesto, e Rollback instructions) e na seção Post deployment dos 5 PRs; itens 4 e 9 só em `deployment-instructions.md`. No prod-2, os dois Jenkins que rodam o `payout-delay` (job `payout-delay` e a opção `wallet-payout-delay` do job `jobs`) não rodam durante o deploy. Falta reescrever os passos 3 e 5 do manifesto (sdd-release, depois do 409) | Lucas |
| 2026-11-17 | preprod | o CLS-1214 vai a preprod depois do review humano aprovado; a pergunta do passo 15 está respondida | Lucas |
| 2026-11-17 | 4755: `pcw-51` vermelho no CI da wallet | já existia no master, mesmo teste e mesmo job (`proteus / isolated-tests`, "Claim a promotion bonus in a currency the brand does not accept from service API (OpenAPI)", `bonusTransaction.pcw-51.test.ts:315`): [run 43883501580 de 16/11 no `45684ffdd`](https://github.com/celesta-tech/celesta-wallet/actions/runs/43883501580) e [run 43224438665 de 12/11 no `e9120437a`](https://github.com/celesta-tech/celesta-wallet/actions/runs/43224438665). Run do #1971 com só ele vermelho: [44038994785](https://github.com/celesta-tech/celesta-wallet/actions/runs/44038994785). Não é desta mudança | Claude (conferido nos logs) |
| 2026-11-16 | review por sub-task | sem o review nosso por agente sem contexto em cada sub-task: 4753 e 4754 vão a To review direto; o review da story inteira roda quando o 4755 fechar | Lucas |
| 2026-11-16 | 4754: migration | `INSTANT` só no `up()`, `down()` segue `INPLACE`; plano emendado (`61cf5b922`) | Lucas |
| 2026-11-16 | 4753: lista maior que a coluna | o plano dizia que o save falha antes do banco; só vale em MySQL strict, e o preprod roda `NO_ENGINE_SUBSTITUTION` (corta em silêncio, a guarda descarta, os não-lead podem ser pagos de novo). Decisão: validar no form o tamanho da lista codificada contra os 512 da coluna, 400; sem teto de quantidade, sem constante. Strict na conexão descartado (muda todo insert do payment). O 4755 já trata a rejeição (grupo inteiro em error) | Lucas |
| 2026-11-16 | 4754: lista, fallback, tipos, nome, CSV | coluna JSON re-encodada (malformada → NULL); fallback só na leitura, sem backfill; fallback vale para todo tipo de movimento (muda 13/11, que era só `withdraw`: uma regra a menos); `withdrawRequestIds` no OpenAPI; CSV fora; migration `Version20261408000001` | Lucas |
| 2026-11-16 | 4755: onde fica o grupo | coluna `payout_group_id` na `withdraw_request` e na audit (muda 13/11, que era `additional_data`: o `jsonSerialize()` vaza para BO e gateway, e o PATCH faz merge nele) | Lucas |
| 2026-11-16 | 4755: membro fora de processing | grupo inteiro em error no pre-flight (muda 13/11, "paga o resto": valor diferente do grupo registrado, caminho de dinheiro) | Lucas |
| 2026-11-16 | 4755: rollout da wallet | suspender o CronJob `withdraw-request:payout-delay` antes do deploy da wallet e retomar com todos os pods novos. Vai nas instruções de deploy e no manifesto de release como ação manual. Sem flag | Lucas |
| 2026-11-16 | 4755: lead | o menor id do grupo | Lucas |
| 2026-11-13 | plano do 4758 agora | adiado: o cleanup só sai quando o 4757 estiver em produção; gate 1 só com 4753–4757 | Lucas |
| 2026-11-12 | planos da story juntos (decisão de 11/11) | cai: plano espera o push do plano que ele lê. A execução não segura vários rascunhos, e o contrato nasce em cadeia | Lucas (a confirmar) |

## Estado

- 2026-11-13 11:41: rascunhos 4753–4757 com as respostas do gate 1 aplicadas e conferidas (migration do 4754
  `Version20261408000001`, na sequência do repo; teto de 512 do payment como edge case). Falta o "sim" do Lucas.
- 2026-11-13 ~13:20: sessão de execução parou no reinício do painel com a faixa 844–904 do transcript não lida.
  Antes de reenviar o "sim", conferir se ela começou a escrever planos (branches CLS-4753..4757 no origin).
- 2026-11-13 (tarde): o "sim" do gate 1 foi enviado às 11:41. A sessão criou as branches locais CLS-4753..4757
  nos worktrees `/tmp/cls1214/<KEY>` (de origin/master fresco), escreveu `.sdd/_plans/CLS-4753.md` (idêntico ao
  rascunho) e parou no commit+push, antes do reinício. Nada no origin. No 4753, `tests/Stubs/DdTrace.php`
  aparece modificado: é a falsa alteração do Mac, nunca entra no commit.
- Prioridade: CLS-1214 é urgente; CLS-418 fica parado esperando respostas (Lucas, 2026-11-13).
- 2026-11-13 13:32: CLS-4753 commitado local (`CLS-4753: plan`, só o arquivo do plano, sem trailer); push
  esperando permissão quando o Lucas parou tudo para atualizar o Celly. 4754–4757: branch local, nada escrito.
  Retomar pelo push do 4753.
- 2026-11-16: retomado. origin/master andou: payment ganhou o hotfix `hold the transaction lock during a payout`
  (#1434, mesmo `PayoutController::payout()`); nos outros, só o rollback do `[run-ci]` e, no front, a config do jest
  em `jest.config.json`. Plano do 4753 revalidado: sem conflito; corrigida a linha de precedentes de lock (o payout
  já segura dois) e acrescentado o edge case de ordem dos locks. Rebase (via reset + cherry-pick, por causa do
  `DdTrace.php`), push, **PR payment #1435**, label `sdd-plan`. Custo do plano não postado: a sessão que escreveu
  morreu no reinício. Branches 4754–4757 recriadas no master novo, ainda vazias.
- 2026-11-16: worktree `/tmp/cls1214/CLS-4753` removido; a branch está no clone principal do payment (fila de
  implement). Em agentes: `sdd-implement CLS-4753` até o pedido de push (proteus num worktree irmão
  `celesta-qaa-proteus-CLS-4753`); `sdd-plan` 4754 e 4755 nos worktrees de `/tmp/cls1214/`, até o rascunho.
  Os rascunhos de 13/11 ficam em `drafts/` para comparar.
- 2026-11-16: board 4753 → In Progress, pai → Implementing. Gate 2 do 4753 limpo (diff = plano; 2766 testes, só o
  DdTrace; proteus sem `_specs/_plans`, como o #807 do 4933): "sim" ao push. Gate 1 do 4754 limpo: "sim" ao write.
  4755: agendador é o job Jenkins `wallet-payout-delay`, não CronJob; duas correções mandadas (lead fora de
  processing só vai ao processor se ainda `queued`, senão um PayoutJob reentregue erra membro já pago; fee do grupo
  `null` quando todas null). Pré-existente, fora do escopo: payout sem `withdrawRequestId` grava `"null"` e o My.Tu
  manda `"null"` no `msg`.
- 2026-11-16: 4754 escrito, **PR statistics #1063** (só o plano, sem atribuição), label `sdd-plan`, custo $8.28
  postado pelo skill; 4754 → Planned. Rascunho refeito do 4755 em `drafts/CLS-4755-2026-11-16.md`, gate 1 limpo,
  esperando o "sim".
- 2026-11-16: o agendador do `payout-delay` não é Jenkins nem CronJob: é uma linha do crontab da wallet
  (`<env>/wallet/cronjobs/crontab` no celesta-argocd-parameters), rodada pelo supercronic do Deployment
  `wallet-cronjobs`, que recarrega com `-inotify`. O CronJob base é apagado nos overlays do celesta-argocd e
  suspenso no prod-2 (celesta-sb-argocd); o job Jenkins não tem trigger. Ação manual do rollout: tirar a linha do
  crontab antes do deploy da wallet e devolver depois. Correção mandada ao agente; "sim" ao write do 4755.
- 2026-11-16: 4755 escrito, **PR wallet #1971** (só o plano; crontab nos três lugares, nenhum Jenkins), label
  `sdd-plan`, custo $8.52 postado pelo skill; 4755 → Planned.
- 2026-11-16: 4753 push feito (payment #1435 `4400db289` + `c1cf347e9`; proteus #822, hook `qaa-reviewer` não rodou:
  sem `claude` no PATH). Revisão parou na rodada 2: lista longa em MySQL não-strict (decisão acima). CI 99%: linha 854
  do `TransactionRepository` (conjunto vazio) sem teste. Custo do implement $26.67. Próximo: `sdd-plan` emenda +
  implement retoma (validação, teste de 400 no lugar do de strict, cobertura da 854), um CI só.
- 2026-11-16: implements 4754 e 4755 pararam no passo 0 (playbook 0.59.0 instalado, `main` 0.60.0; diferença só na
  checagem de versão). Branches nos clones principais (worktrees de `/tmp` removidos), nada tocado; 4754 e 4755 →
  In Progress. Esperando o Lucas atualizar o plugin. Promotion do 3316 derrubada; backoffice fica (é de outro
  trabalho).
- 2026-11-16: plugin 0.60.0. Reabertos 4753 (emenda (a) + implement), 4754 e 4755 (implements). 4756 escrito,
  **PR backoffice #3339** (só redação compactada em relação ao rascunho aprovado), label, custo $2.21; 4756 →
  Planned. Implement do 4756 só com ok do Lucas (stack do backoffice é do CLS-3094). Rascunho do 4757 em
  `drafts/CLS-4757-2026-11-16.md`, gate 1 limpo (o front deixa de ler `withdrawRequestId` nas 8 leituras),
  esperando o "sim".
- 2026-11-16: coleção Newman montada, **não rodada** (stacks com os implements; roda quando a coordenação liberar):
  `CLS-1214.postman_collection.json` (só gateway e BO), `CLS-1214.dev-only.postman_collection.json` (payment, 400 da lista
  longa), `run.sh`, `CLS-1214.md`. Scripts conferidos contra um stub (81 asserções, 0 falhas). Sem `matrix.md` na pasta: a
  lista de células veio do pedido e dos critérios do pai. Ajustes prováveis no primeiro run: `amount`/`fee` da linha do
  relatório, chave `amount` de `/wallet/transactions`.

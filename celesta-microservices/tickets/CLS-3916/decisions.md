# CLS-3916 — decisões e pendências

## Alias do constants envelheceu, 2026-11-18

`celesta-constants` v1.369 saiu (CLS-5181, outro time). O alias do 4767 é **`dev-CLS-4767 as 1.370`**. A branch `CLS-4767` não tinha o master:
merge do master nela (push no PR #635), depois o bump de alias em 4771 (PR #605) e 4774 (PR #3343); o 4772 já usa 1.370. Antes do release, reconferir
`git tag --sort=-v:refname | head -1` das duas bibliotecas (job-library v3.151, alias 3.152).

## Execução, 2026-11-18: decisões da coordenação

- **4774, Datadog PR Gates / "No new code quality violations"** (avoid empty blocks em `GiftType.php`): não se corrige. Os dois métodos vazios são
  obrigatórios pela classe abstrata, iguais ao `FutureDepositType` do master, e o portão não é obrigatório para o merge. Não suprimir nem mexer no `GiftType`.
- **4774, CI:** `gh workflow run ci.yml -R celesta-tech/celesta-backoffice --ref CLS-4774` só depois do último push dos revisores (hoje: falta o commit da correção da
  rodada 1, que o Lucas faz no clone principal, `CLS-4774/gate2.md`).
- **Board:** 4774, 4772 e 4775 em In Progress (2026-11-18). 4767, 4768, 4770 e 4771 em To review.
- **4769:** rodada 1 do review com 2 should-fix de testes que pedem emenda de plano (fixture `user` com 7301, mensagem com `reason_id` nil); aguardam decisão.

## Gate 1 fechado, 2026-11-17: planos em PR

Todas as "pending" dos cinco rascunhos viraram "answered by Lucas Franco, 2026-11-17"; só a #6 (coluna em vez de `Source`)
foi provisória e foi tirada: decisão técnica, final. Fora do plano, por pedido dele: fila SQS de activity (ele pede ao Team O),
evento que não volta após falha da wallet com Instant Reward marcando `rewarded` (ticket próprio), título e descrição do 4770 no Jira (ele cuida).

| Sub-task | PR | Worktree |
|---|---|---|
| 4770 promotion | celesta-promotion #604 | `/private/tmp/cls3916/celesta-promotion-4770` |
| 4771 promotion | celesta-promotion #605 | `.../celesta-promotion-4771` |
| 4772 promotion | celesta-promotion #606 | `.../celesta-promotion-4772` |
| 4774 backoffice | celesta-backoffice #3343 | `.../celesta-backoffice-4774` |
| 4775 backoffice | celesta-backoffice #3344 | `.../celesta-backoffice-4775` |

- 4773 não planejado (sem trabalho). Fechar a sub-task é escrita no Jira, só com pedido.
- O PR e o H1 do plano do 4770 usam "Gift source_promotion_id column and sourcePromotionId in the gift API", não o resumo do Jira (ainda fala de `Source`).
- Jira: label `sdd-plan`, transição para Planned e comentário de custo nas cinco. Custo = transcript do agente de plano (4772 com 2 runs); 4774 e 4775 não somam o rascunho de 2026-11-16.
- Base do 4772: no implement, mergear `origin/CLS-4743` (#602), `CLS-4770` e `CLS-4771` na `CLS-4772`; os PRs dos irmãos mergeiam antes.
- 4771 e 4772 no mesmo grupo de deploy. 4774 não tem o link Blocks 4771 → 4774 no Jira (só com pedido).

## Infra e dependência do 3316 (2026-11-17)

- **Fila de activity: nada a mudar na infra.** A fila `<prefixo>activity` já existe nos 7 ambientes (terraform
  `sqs.tf`; o celesta-activity lê dela). Em todos, a promotion usa a mesma conta SQS, a mesma chave e o mesmo
  `SQS_QUEUE_PREFIX` do activity (`celesta-argocd-parameters/<env>/{promotion,activity}/parameters.yaml`), e a
  policy SQS de cada conta é `Resource: "*"` (`celesta-prod-1-sqs`; a spec CEL-8712 do terraform diz o mesmo).
  O transport `activity_sqs` do plano do 4772 funciona sem pedido ao Team O.
- **CLS-3316:** o código precisa dele (o gift copia o `reasonId` da config, que só existe no CLS-4743); o plano
  do 4772 já mergeia `origin/CLS-4743`. Nas instruções de deploy: o CLS-3316 inteiro em produção antes do 3916.
- Manifesto e DI: ficam com a coordenação, entram no prompt de execução.

## Respostas de 2026-11-17 (coordenação, Lucas)

"Provisória" = decisão tomada para o plano seguir; pode mudar depois da reunião com o Francisco. No plano,
entra em Decisions como "Lucas Franco, 2026-11-17", com a frase "pending product owner confirmation" nas
provisórias. Nada disso vai para o Jira, e a spec do pai não é editada: mudança de AC é proposta depois.

| # | Pergunta | Decisão | Tipo |
|---|---|---|---|
| 1 | Editar, concluir e cancelar o gift de promoção | Construído só pelo CLS-3865. O AC "can be edited, completed and canceled like any claimed gift" é dependência de teste: verificado depois do 3865 e do 3508. Nenhum plano do 3916 implementa isso | final |
| 2 | Gift pulado (config desativada ou apagada na premiação) | Só log, como a spec diz ("skip logged with reason"). Outros prêmios da faixa saem, instância `rewarded`, **sem exceção** (matriz 22 e 23) | final |
| 3 | `bonus_offer_allowed = false` | **Não cria o gift** (Lucas, 2026-11-17, revendo o "sim" provisório do Francisco). Comportamento de hoje: o flag barra a premiação inteira (`Validator/Reward/BonusOfferAllowedValidator.php:27`; RAF em `ReferAFriend/Handler/RewardHandler.php:121,134,241`), então o 4772 não precisa de tratamento especial. **Correção (2026-11-17, Lucas):** `bonus_offer_allowed` não é o status do jogador. É um flag da wallet que o operador liga e desliga no BO (`WalletType::bonusOfferAllowed`, backoffice `WalletController`). O AC "Player status: ... whatever the player's status" fala do status da conta e continua certo: a premiação da promotion não confere status de conta (grep sem achado; só KYC no RAF). Não é contradição: falta um AC próprio para o flag, a propor ao Francisco | final |
| 4 | Offering status inativo | Não se aplica: config de gift não tem período nem recorrência, então é sempre `active` | final |
| 5 | Motivo | O gift copia o `reasonId` da config; nenhum se a config não tiver | final |
| 6 | Entidade `Source` × coluna | Coluna nullable `source_promotion_id` ao lado de `source_user_id` e `source_scenario_id`. Sem entidade, sem backfill, sem drop: o CLS-4770 vira só a coluna; o CLS-4773 não tem trabalho (não planejar; fechar a sub-task é escrita no Jira, só com pedido do Lucas) | **provisória** |
| 7 | Contrato 4774 × 4776 | O 4774 aceita `rewardConfigurationId` **ou** `bonusModelId`, como os outros tipos | final |
| 8 | Ordem de deploy | 4771 e 4772 no mesmo grupo (matriz 38) | final |
| 9 | RAF com reprocesso | Um gift por destinatário, nunca dois (matriz 25), critério do plano do 4772 | final |
| 10 | To review de 4767 e 4768 | Com `sdd-reviewed` e teste local verde; o CI das bibliotecas só roda quando o PR é aprovado | final |
| 11 | Assignee das sub-tasks | Não mexer agora | final |

Em aberto, sem bloquear o plano: o buraco de split do front (ID e link da promoção em "created by", label
`promotion` nos 6 locales, filtro de source).

## Gate 1, 2026-11-16 (Lucas)

| Sub-task | Decisão |
|---|---|
| 4767 | sem tarefa de tag; sem teste da constante; enum do OpenAPI do gateway só como nota em Edge Cases |
| 4768 | `sourceUserId` = id da configuração de promoção; id da instância, se precisar, em `additionalData` (4772); sem tarefa de tag |
| 4769 | branch `CLS-4769`; uma linha em Edge Cases sobre o PR #515 (fixtures em `database/fixtures/`) |

PRs de plano (worktrees em `/private/tmp/cls3916/`), as três em Planned: 4767 constants #635 (`dev-CLS-4767 as 1.369`),
4768 job-library #561 (`dev-CLS-4768 as 3.150`, alias disputado por #556/#554/#550), 4769 activity #525.

Link Blocks 4768 → 4775 criado no Jira (o filtro de logs do BO valida contra `UserActivityJob::SOURCE_TYPES`).

## Gate 1 do BO (4774, 4775), rascunhos em `drafts/`, aguardando o Lucas

- **Conflito de contrato 4774 × 4776.** O rascunho do 4774 exige `rewardConfigurationId` (NotBlank) no gift.
  O plano do front (`origin/CLS-4776`, `.sdd/_plans/CLS-4776.md:43`) manda `{type: "gift", bonusModelId}`.
  Do jeito que está, o save do front daria 400. Proposta: o 4774 aceita um dos dois, como os outros tipos.
- **Para o plano do 4772.** O `additional_data` do `gift_offered` precisa das mesmas chaves que o BO manda
  (`UserActivityJobManager::dispatchGiftOfferJob`): `gift_id`, `reward_configuration_id`, `name`, `value`,
  `currency`, `reason_id`, `reason_name` e `description`. Sem `reason_name` e `description`, o log não
  mostra o motivo nem a nota.
- **Buraco de split no front.** Nenhuma sub-task cobre: o ID e o link da promoção em "created by" (critério do
  pai), o label `promotion` da source de activity nos 6 locales e a entrada `promotion` no filtro de source.
  O 4776 só cobre o picker.
- **Link que falta no Jira:** o 4771 bloqueia o 4774. Não mexo no Jira sem pedido.

## Para o manifesto de release (`releases/CLS-3916.yaml`)

O `sdd-release` recusa sub-task sem PR, então isto entra quando o 4771 rodar o release:

- **4771 e 4772 no mesmo grupo de deploy.** `RewardAmountCalculator.php:23` lança para tipo desconhecido e
  `RewardHandler.php:234` não pega: com o 4771 sozinho em produção, uma faixa com gift falha a premiação
  inteira, bônus incluídos. Matriz, caso 38.
- Troca de pin da constants (4767) e da job-library (4768) no release de quem consome (4771, 4774, 4772, 4775).

## Buraco de split fora deste pai

- celesta-scenario: a ação de bônus do cenário precisa mandar o motivo (CLS-3316). O pai já tem spec, então
  é proposta de sub-task ao PO, não plano em cima (Lucas, 2026-11-16).

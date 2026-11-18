# CLS-3250 — reunião de gifts com o Francisco

Preparação, 2026-11-17. Leitura e explicação: nada foi escrito no Jira, no Slack nem em PR.

Código lido do `origin/master` (promotion `94cd950b4`, constants e wallet idem, fetch de hoje; master local
já estava igual e limpo). Fontes de memória: `CLS-4163`, `CLS-419-CLS-3392`, `CLS-4540`, `CLS-2594-CLS-3055`,
`CLS-3916/readiness`. Fontes de ticket: `tickets/CLS-3916/`, `tickets/CLS-3865/`, `tickets/CLS-3316/`.

Quatro stories do épico: **3316** (reasons nos bônus, em review), **3916** (gift como prêmio de promoção,
parado nas respostas), **3865** (editar valor e concluir gift, página Gifts to order), **4742** (assets
ligados na página da reward configuration). Ordem: 3316 bloqueia 3916; 3916 antes do 3865 (os dois migram a
entidade gift e os planos 4940/4941 leem as migrations 4770/4773).

---

# Parte 1 — como as peças se organizam hoje

## Em uma frase

A Celesta dá coisas a jogadores. A **promotion** decide *o que* dar e *quando*; a **wallet** guarda o saldo
de quem recebeu. O **gift** é o único prêmio que não passa pela wallet.

## Diagrama

```
 PromotionConfiguration ──< RewardAggregator ──< Reward ──┐        (a campanha e seus prêmios)
   (campanha: tipo, status,        (faixa/regra)   (linha de prêmio)   │ N:1, nula se a config for apagada
    segmento, limites)                                                 ▼
        │ 1:N                                          RewardConfiguration  (o modelo reutilizável de prêmio)
        ▼                                                 type: free | deposit | free_rounds | gift
    Promotion  (instância por jogador:                    status enabled/disabled, offering_status,
     engaged → rewarded | expired)                        stock, currency, reason (chave legada)
        │ promotion_id (nulo se não veio de promoção)         ▲ N:1                    ▲ N:1 (nula)
        ▼                                                     │                        │
      Bonus ─────────────────────────────────────────────────┘                      Gift
   (o prêmio dado ao jogador:                                            (anotação de presente físico:
    offered/claimed/played/                                               nome, valor, moeda copiados da
    canceled/expired)                                                     config; só `claimed`)
        │ ao virar claimed: promotion posta                                  │ reason_id (N:1)
        ▼ "claimed" na wallet                                                ▼
   sub_balance (wallet, BonusSubBalance,                              RewardOfferingReason
    com bonus_id; mesmos status)                                      (motivo por marca, soft delete)
```

Reward configuration **não é uma tabela por tipo**: é uma tabela só com a coluna `type`. Só free rounds tem
extensão (`FreeRoundConfiguration`, uma subclasse por provedor).

## Peças, uma linha cada

| Peça | O que é | Estados |
|---|---|---|
| PromotionConfiguration | a campanha (deposit tier, first bet insurance, refer a friend, instant reward, multiplus) | `enabled`, `disabled` |
| Promotion | uma instância: o jogador entrou na campanha | `engaged`, `rewarded`, `expired` |
| RewardAggregator | faixa ou regra dentro da campanha (tier, bet_result, papel do RAF) | — |
| Reward | linha de prêmio: tipo (`free_bonus`, `free_round`, `match_deposit`, `match_bet`, `future_deposit`), opções, aponta para uma reward configuration | — |
| RewardConfiguration | o modelo do prêmio, reutilizado por cenário, oferta manual e promoção | `status` enabled/disabled; `offering_status` active/inactive (mantido por listener, regra não lida); soft delete |
| Bonus | o prêmio concreto dado a um jogador | `offered` → `claimed` → `played`; `canceled` e `expired` a partir de offered/claimed; `played` volta a `claimed` |
| Gift | anotação de presente entregue **fora** do sistema (ingresso, jantar). Não credita carteira, não notifica | só `claimed` no master |
| RewardOfferingReason | motivo da oferta, por marca, nome até 64 caracteres | ativo ou soft-deleted |
| sub_balance (wallet) | o bônus do lado da carteira, com `bonus_id` | os mesmos status do bônus |

## Por onde cada um nasce

| Origem | Caminho | Resultado |
|---|---|---|
| Oferta manual (BO) | `POST …/player/{id}/reward-configuration/{id}/offer`, com `sourceUserId` | Bonus `offered`; vira `claimed` quando o jogador resgata, ou na criação se a config for `claiming_event = automatic` |
| Bulk | o BO chama o mesmo endpoint de oferta, jogador a jogador (pelo que o CLS-3316 registra; **não está no código da promotion**) | idem |
| Scenario | a ação *Offer reward* chama o mesmo endpoint com `sourceScenarioId`; bônus ambíguo (user e scenario juntos) dá 400 | idem |
| Promoção | o handler da campanha chama `offerForPromotionReward` por linha de prêmio, com `promotion_id` | Bonus; a instância vai a `rewarded`. **Config de gift é recusada** (no save e na emissão) |
| Gift direto | `POST …/player/{id}/gift` com `rewardConfigurationId` de uma config **gift**, `sourceUserId` ou `sourceScenarioId` (um só); lê a wallet só para saber as moedas; confere estoque e idempotência | Gift `claimed`, 201 |
| Gift request | **não está no master.** Promotion #591 (CLS-4540): request com aprovação; o approve cria o gift pelo mesmo caminho do offer | — |

Dois pontos que confundem:

- No master, `RewardOfferingReason` só é usada pelo **gift**. A reward configuration e o bônus ainda guardam o
  motivo como a chave legada (`reason`, 31 chaves fixas). O CLS-3316 (promotion #602, em review) troca isso por
  `reason_id`.
- O gift copia nome, valor e moeda da config na hora (`GiftFactory`). Editar a config depois não muda o gift.

## O que ainda não está no master

| Peça | Ticket | Onde |
|---|---|---|
| gift request e approve | CLS-4540 | promotion #591 |
| cancelar gift (`canceled`) | CLS-3508 / CLS-4434 | promotion #592 |
| concluir e editar gift (`completed`) | CLS-3865 | sem plano ainda |
| `reason_id` em config e bônus | CLS-3316 / 4743 | promotion #602 |
| gift como prêmio de promoção | CLS-3916 | planos 4767, 4768, 4769 em PR |

## Não verificado

- O que a wallet faz ao receber o `claimed` (existe `ClaimHandler`; não li a criação do sub_balance).
- A regra do `offering_status` (só o listener que o dispara).
- O caminho do bulk dentro do BO.

---

# Decisões do Lucas, 2026-11-17

Perguntas que saíram da lista porque o Lucas decide, ou porque o código já responde.

| Tema | Decisão | Por quê |
|---|---|---|
| 3916: editar, concluir e cancelar o gift de promoção | não pergunta. Quem constrói é o 3865; o critério do 3916 só é verificado depois do 3865 e do 3508 | o 3916 diz só "like any claimed gift": é dependência de teste, não definição duplicada |
| 3916: gift pulado | só log, como a spec já diz ("skip logged with reason"; a métrica conta "one logged skip") | a rota do jogador não mostra gift, então o produto não promete o item; quem perde é a operadora, que não vê o item na fila |
| 3916: offering status inativo | pergunta descartada | config de gift não tem período nem recorrência (`GiftRewardConfigurationType`), então o `offering_status` é sempre `active` (`RewardConfigurationService.php:57`) |
| 3865: gift pendente concluído depois do release | segue o fluxo novo e conta na conclusão | **quebra:** gift criado antes do release já contou na criação e conta de novo. Contradiz o AC "completing it doesn't count it again". O Lucas confere em produção: `SELECT domain_id, status, COUNT(*), SUM(amount) FROM gift GROUP BY domain_id, status;` (a tabela foi zerada no deploy do CLS-4163). Sem `claimed`, nada quebra e o AC sai |
| 3865: duas ações ao mesmo tempo | padrão do gift: transação com trava de linha (`GiftService::changeStatus`, CLS-4434). Editar × editar: vale a última. Transição × qualquer: o segundo falha pela máquina de estados. Cada ação bem-sucedida grava evento na activity | contradiz o AC "the second gets an error", que precisa ser reescrito |

## Para o Francisco (lista final)

1. **CLS-3916.** Jogador com `bonus_offer_allowed = false` recebe o gift da promoção? Hoje nada é premiado nesse caso, e a spec diz "as for promotion bonuses". Recomendação: manter como hoje e reescrever o AC.
2. **CLS-3865.** Gift checkout com mais de 100 gifts deve paginar? Recomendação: sim.
3. **CLS-3865.** O Adjustment da página Gift checkout da branch do Dimitris (CLS-4545) está fora do escopo? Construímos em cima dessa página ou do zero?
4. **CLS-3865, aviso.** Dois ACs mudam pelas decisões acima: "completing it doesn't count it again" (se houver gift em produção) e "the second gets an error".

---

# Parte 2 — perguntas para a reunião

Perguntas em inglês, prontas para falar ou colar. Contexto e recomendação em português.

Aviso: o "texto ao PO" do CLS-3316 **não existe escrito** em `sdd.md` (só o lembrete "texto ao PO espera",
linhas 230, 242, 265, 319). Escrevi as duas perguntas abaixo a partir das notas e dos rascunhos 4743/4744.
Confira antes de usar.

---

## CLS-3916 — gift como prêmio de promoção

Já postadas no Jira (comentário 92818). Lidas de `tickets/CLS-3916/questions-po-tl.md`, não do Jira.

### Para o Francisco (PO)

**1. Gifts to order (matriz #42)**

> Gifts to order says "edited, completed and canceled", but that is CLS-3865, still in Split and not linked here, and `claimed` is the only status in code. Does this story wait for it, or do those acceptance criteria move there?

- Contexto: o AC do 3916 cita o ciclo de vida que só o 3865 constrói.
- Recomendação: mover esses AC para o 3865 e ligar as duas stories.

**2. Gift pulado, quem vê? (matriz #22 e #23)**

> When the gift is skipped (configuration disabled or deleted at rewarding time), is an application log enough, or must the operator see it, say on the promotion instance or in player activity?

- Contexto: o bônus da faixa sai, o gift é pulado e a instância fica `rewarded`. Só com log, ninguém encomenda o item e ninguém percebe.
- Recomendação: uma entrada de player activity. Se for só log, escrever isso no AC.
- Caso 23 (config apagada na premiação): decidimos pular sem lançar exceção, como o bônus faz hoje com config nula. Sai junto com esta resposta.

**3. Status do jogador (matriz #26)**

> Every promotion type checks the wallet flag `bonus_offer_allowed` before rewarding. When it is false nothing is rewarded, so no gift either. "As for promotion bonuses" means blocked by this flag. Should the gift still go through?

- Contexto: a spec diz que o status do jogador não barra o gift "como no bônus de promoção", mas o bônus **é** barrado.
- Recomendação: manter o comportamento de hoje (barra) e reescrever o AC.

**4. Offering status (matriz #27)**

> Enabled gift configuration, offering status inactive at rewarding time: give or skip?

- Contexto: a spec não fala; o bônus de promoção hoje ignora o offering status.
- Recomendação: dar o gift, igual ao bônus.

**5. Motivo**

> CLS-3316 gives every reward configuration, gift ones included, a `reasonId`. Unless you object, we copy it onto the gift, none if the configuration has none, and this part waits for CLS-3316.

- Contexto: o CLS-4743 dá `reasonId` à config de gift; o gift copia.
- Recomendação: seguir assim. Só confirmar que não há objeção.

### Para o Marcello (TL)

**6. Entidade `Source` ou coluna (4770, 4773)**

> CLS-4770 and CLS-4773 add a `Source` entity, backfill every gift and drop columns a release later. The alternative is a nullable `source_promotion_id` next to `source_user_id` and `source_scenario_id`: no backfill, no drop, no CLS-4773, and the raw SQL replay keeps working. Is a fourth origin planned that justifies `Source`? If not, I'd go with the column.

- Contexto: `Gift.php:81-86` e o replay de idempotência em SQL cru (`GiftController.php:325-326`).
- Recomendação: a coluna. Sem backfill, sem drop, sem o 4773.

### Achados da matriz, sem pergunta no comentário

| Caso | O que é | De quem | Recomendação |
|---|---|---|---|
| 25 | RAF: referrer premiado, referee falha, o evento volta | só ciência do Marcello | virou critério do plano do 4772: um gift por destinatário, nunca dois no reprocesso. Sem decisão a tomar |
| 38 | `RewardAmountCalculator` lança para tipo desconhecido e a premiação **inteira** falha, bônus incluídos | Marcello (ordem de deploy) | 4771 e 4772 no mesmo grupo do release. Sem isso, uma faixa com gift perde também os bônus |

---

## CLS-3865 — editar o valor do gift e concluir (Gifts to order)

Lidas de `tickets/CLS-3865/matrix.md` e `understand/evaluate-CLS-3865.md`. Nenhuma foi postada ainda.

### Para o Francisco (PO)

**1. Gift em produção antes do release (matriz #19, #24, #44, #45, #46, #50)**

> Is there any gift registered in production today, and in which brands? The spec says completing an old gift does not count it again and past periods do not change, but CLS-4938 says there is no special rule for older gifts because the feature is not used yet.

- Contexto: a spec e o 4938 se contradizem. Um dos dois muda. Sem a resposta, seis células da matriz ficam sem classe.
- Fato a conferir: ninguém nosso lê o banco de produção, então a confirmação vem dele ou do Marcello.
- Recomendação: se não existe gift em produção, tirar o AC "Gift recorded before release" e deixar o 4938 como está. Se existe, precisa da regra, e o job `player_kpi_eow` do BI reescreve 7 dias (célula 50) e muda partição anterior ao release.

**2. Status `offered` (achado 4 da matriz)**

> The spec and CLS-3508 mention an `offered` gift status. It exists in the front labels only: the backend creates gifts as `claimed`. Can we drop `offered` from the text?

- Contexto: `GiftConstants` no master só tem `claimed`; o front tem label e botão de cancel para `offered`.
- Recomendação: sim, tirar. Confirmação rápida.

**3. Editar para o mesmo valor (#16)**

> If the operator edits a gift to the value it already has, should we accept it quietly or return an error?

- Contexto: aceitar grava um evento `gift_value_edited` com valor antigo igual ao novo.
- Recomendação (minha): 200 sem gravar evento. Erro confunde o operador e evento old = new suja o log.

**4. Gift de scenario na lista, "created by" (#22)**

> A gift offered by a scenario has no back-office user, so "created by" is empty. Should it show a dash, or the scenario?

- Contexto: `source_user_id` é nulo; a spec lista os casos de "—" e não inclui scenario. O 3916 vai criar a mesma pergunta para o gift de promoção (#23).
- Recomendação: mostrar a origem ("Scenario 12", depois "Promotion 34"), não um traço.

**5. Mais de 100 gifts claimed (#29)**

> The list returns at most 100 gifts by default and the spec says nothing about paging. If there are more than 100 gifts to order, should the page paginate?

- Contexto: `GiftRepository.php:29,140-142`. Sem paginação, os gifts mais novos somem da fila em silêncio.
- Recomendação: paginar. A lista já aceita `limit` e `offset`.

**6. Quem tem só `PS_GIFT_REQUEST_VALIDATE` (#55)**

> A user with only the permission to validate gift requests does not see Gifts to order. Is that intended?

- Contexto: o validador de requests vê a página de requests, não a fila de encomenda.
- Recomendação: sim, é intenção. Confirmar.

**7. Editar × editar sem erro (#32)**

> The acceptance criteria say that when two operators edit the same gift, the second gets an error. Today the lock serializes them and the second just overwrites. An error needs the request to carry the value the operator saw. Do we want that, or is last write wins fine?

- Contexto: o lock pessimista da 4434 serializa, mas não dá erro entre duas edições. Concluir × editar e concluir × concluir já funcionam como a spec diz.
- Recomendação: relaxar o AC para last write wins, com os dois eventos no log. Um erro de conflito pede contrato novo (valor esperado ou versão) para um caso raro.

**8. Página "Gift checkout" do CLS-4545 (Dimitris)**

> The front already has a Gift checkout page (CLS-4545) with Edit value, Complete, Cancel and Adjustment. It calls routes the backoffice does not have, and Adjustment is not in any ticket. We plan to ignore that front and build Gifts to order from CLS-3865. Can you confirm Adjustment is out of scope and that this page is replaced?

- Contexto: a página chama `POST /gift/{id}/complete`, `PATCH /gift/{id}` e `POST /gift/{id}/adjustment`, que não existem no BO. O 4943 e o 4944 partem dessa branch.
- Decisão do Lucas: ignorar esse front. Falta a confirmação do Francisco.
- Recomendação: Adjustment fora, e avisar o Dimitris para não manter a página em paralelo.

### Para o Marcello (TL)

Só a parte de fato da pergunta 1: alguém com acesso lê em produção se existe gift, e em quais marcas.

---

## CLS-3316 — reasons nos bônus

O texto não estava escrito. Rascunho a partir de `sdd.md`, `drafts/CLS-4743.md` e `drafts/CLS-4744.md`.

### Para o Francisco (PO)

**1. Seed só das chaves que cada marca usa (4744, Q2)**

> The acceptance criteria say each brand ends up with its previous reasons plus the legacy ones. The migration seeds, per brand, only the legacy keys its configurations actually use, not all 31. A brand that never used `raf` will not have a `raf` reason. Is that fine?

- Contexto: o AC fala em "previous reasons plus the legacy reasons". O 4744 semeia só o que cada marca usa (inclusive chave fora da lista fixa), então a lista de motivos não vira 31 linhas de ruído por marca.
- Recomendação: sim. A marca cria o que faltar à mão. Marca sem configuração começa vazia, como a de hoje.

**2. Oferta manual com reason apagado da config (4743)**

> A reward configuration keeps a reason that was deleted later. When someone makes a manual offer from it, the offer carries that deleted reason and we accept it, but we refuse any other deleted reason. The acceptance criteria say a deleted reason is refused. Do we accept the configuration's own deleted reason?

- Contexto: o 4743 aceita o reason apagado quando é o da própria config (`$kept`), porque o bulk e o front mandam esse. Qualquer outro reason apagado, desconhecido ou de outra marca é recusado. O AC diz só "recusado".
- Recomendação: aceitar o da própria config. Recusar travaria toda oferta daquela config até alguém editá-la.

**3. Motivo nas tabelas de configuração do BigQuery (4747, Q4)**

> In BigQuery, each bonus now carries its reason name. The reward configuration and promotion reward configuration tables still carry the old key. Do you need the reason name there too?

- Contexto: o 4747 só troca a tabela de bônus. As duas tabelas de configuração ficaram de fora, e a decisão foi devolvida ao PO.
- Recomendação: só se alguém lê o motivo pela configuração. Senão, nada muda.

### Já postado, não repetir

Comentário 92819 no CLS-3316: a ação de bônus do scenario precisa mandar o reason, sem sub-task. Virou o CLS-5130.

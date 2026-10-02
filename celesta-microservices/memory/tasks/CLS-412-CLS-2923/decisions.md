---
name: cls-412-cls-2923-decisions
description: "CLS-412-CLS-2923 (celesta-promotion, offer sem BO user, idempotente e atribuído ao cenário) — estado em 2026-09-30, as decisões de desenho, o contrato com o celesta-scenario e o que falta"
metadata: 
  node_type: memory
  type: project
  originSessionId: 00170055-795b-4ad9-bb66-c5e084632793
  modified: 2026-10-01T14:22:00.589Z
---

Ticket filho do épico CLS-412 ("Offer bonus as a scenario action"). Artefatos em
`celesta-promotion/sdd/_specs/CLS-412-CLS-2923.md`, `sdd/_plans/` e `sdd/_how_to_test/`.

## Estado em 2026-09-30, fim do dia

Implementação do promotion **completa e verde, não commitada**. PR #535 aberto, comentários do
Copilot e do Socrates aplicados e respondidos, master mergeado. Último run: phpunit 1647/1647, behat
1034/1034, Newman 9 requests / 24 assertions com 0 falhas, `make lint` exit 0.

**O escopo mudou neste dia.** O PO falou com o Lucas e com o Pedro: entram o `source_scenario_id`
(ver decisão H) e o endpoint de gift — mas o gift **saiu para o CLS-3230, do Bohdan**, não é nosso.

Pendências quando retomar:
1. Commitar o promotion.
2. O backoffice: branch `CLS-412-CLS-2923` já criada a partir do master (`63cb399fb5`), **vazia**.
   Falta somar `sourceScenarioId` e `sourceUserId` ao whitelist do
   `GatewayBundle/Normalizer/Promotion/BonusNormalizer.php` — sem isso o campo morre lá e a AC do
   épico não fecha. A coluna na tela é front, ticket de outro.
3. Avisar o Pedro de duas coisas: o `REFUSAL_STATUSES = [400, 404]` dele precisa do **422**, e a
   `description` da action fica do lado dele (ver abaixo).
4. Flag `move_bonus_to_promotion` foi ligada no flipper local; reverter se incomodar.
5. **Nota do Lucas, 2026-10-01:** na resposta, só os dois sources (`sourceUserId`, `sourceScenarioId`)
   vão em camelCase; o campo de idempotência **não**. Chegou numa sessão de outro ticket
   (CLS-2847-CLS-2848), então pode não ter sido aplicada ainda onde se trabalhava no CLS-412.

## As 4 decisões

| # | Decisão |
|---|---|
| A | `sourceUserId` vira opcional, `source_user_id` fica `NULL` |
| H | **Revertida em 2026-09-30:** o bônus passa a guardar `source_scenario_id`, coluna nullable ao lado de `source_user_id`, devolvida no payload. Duas colunas, não `source_type` + `source_id` polimórfico — esse obrigaria backfill de toda a tabela e quebraria quem já lê `sourceUserId`. Mandar as duas na mesma chamada é **400 `AMBIGUOUS_OFFER_SOURCE`**: preferir uma em silêncio grava origem errada que ninguém detecta depois |
| B | Idempotência por **chave do caller**: `idempotencyKey` no corpo (nome escolhido **pelo Pedro**, 2026-09-25), coluna `idempotency_key` VARCHAR(64) no `bonus`, índice único `(player_id, reward_configuration_id, idempotency_key)` |
| E | **Um só corpo de erro**: `message` + `code`, com `error` e `errors` mantidos como legado |
| G | **201 quando cria, 200 quando repete** — o caller não tem outra forma de distinguir, o corpo é idêntico. Não diz se *ele* já gravou a activity dele; isso só ele sabe |
| F | **404 deixa de absorver falha de upstream**: só um 404 real do Memberzone é `PLAYER_NOT_FOUND`; qualquer outro status, Memberzone inacessível, e payload sem domain id viram **503 `UPSTREAM_UNAVAILABLE`**. `TypeError` sai do grupo e passa a 500 de verdade |
| C | ~~`BonusOfferAllowedCondition` rodar em config `manual`~~ — **descartada em 2026-09-25**, ver abaixo |
| D | `OfferEligibilityException` vira **422** com `{"errors":[msg],"code":"<CODE>"}` (os 5 `CODE_*` já existem); 409 segue significando só "bônus é do Wallet" |

**Por que a C caiu, e o que isso revela.** O enquadramento do Lucas: o cenário é a bulk action do BO
automatizada — um operador escolhe fazer aquilo e para quem. A bulk action não checa
`bonus_offer_allowed` em config manual, então o cenário também não deve; dar regra mais estrita ao
caminho automático que ao botão do operador é mudança de comportamento que o ticket não pediu, e
vazava para fora do endpoint (`DepositRewardClaimService` engole a exceção).

A consequência que isso expõe: como a chain **não roda em manual** e o cenário só seleciona manual,
**nenhum dos 5 códigos de `OfferEligibilityException` acontece no caminho do cenário**. A decisão D
continua certa (recusa de negócio virando 500 é bug) mas serve o caminho automático, do BO. O que o
cenário precisa mesmo é do **envelope consistente**: hoje temos `error` no singular em 3 lugares e
`errors` no plural em outros 3, e as recusas que ele realmente vê são moeda ausente, moeda
divergente, config desativada, jogador desconhecido e flag desligada — nenhuma delas passa pelo 422.

**Por que a chave é do caller e não derivada** — o argumento que fecha a questão, e que o ticket não
tinha: `RewardOfferService::calculateOfferingPeriodTo()` devolve `now + N dias` para config manual,
então duas entregas separadas por segundos produzem períodos diferentes e a guarda derivada **nunca
dispara**; e para config automática com `offerPeriodTo` fixo ela dispara **sempre**, bloqueando a
segunda oferta legítima de um `occurrences > 1`. Erra nos dois sentidos, e nenhuma tolerância
conserta os dois. Some a isso o TOCTOU do [[project_cls2450_cls2452_duplicate_subbalance_investigation]],
que é por que a garantia final é índice único e não checagem na aplicação.

**Lock não resolve** — o `ActionJobMessageHandler` do scenario segura lock Redis por
`(playerId, nome da ação)`, mas isso impede simultaneidade, não repetição: a reentrega da fila chega
segundos depois, com o lock já solto. O lock só torna a colisão rara; o índice é a garantia.

**Sobre a decisão E.** O endpoint escrevia `error` no singular em três sítios e `errors` no plural em
outros três, enquanto os atributos OpenAPI dele já referenciavam os schemas partilhados do
`src/Kernel.php:45-79`, que são `message` + `code` — a documentação descrevia um corpo que nunca era
devolvido. Agora tudo passa por um `offerError()` privado. Os dois nomes antigos ficam porque o
`OfferFreeBonusHandler` do backoffice lê `['error']` com fallback para a mensagem genérica da
exceção: removê-los trocaria, em silêncio, uma mensagem útil por uma inútil no ecrã de um operador,
noutro repositório.

**Onde a origem do bónus aparece hoje: em lado nenhum.** O `BonusNormalizer` do backoffice
(`GatewayBundle/Normalizer/Promotion/BonusNormalizer.php:59-77`) devolve 18 campos e **nenhum é a
origem**. O `source_user_id` é gravado pelo promotion e nunca renderizado, nem para utilizador do BO.
Logo "a oferta de cenário aparece sem origem" não é buraco que o CLS-2923 abre — mostrar origem é
funcionalidade nova. E um inteiro sozinho nunca chegaria: sem campo de tipo, o id 42 tanto é o
utilizador 42 como o cenário 42. Quem tem o par `sourceUserId` + `sourceType` é o modelo de activity.

**Por que a F existe, e por que não é igual à C que caiu.** O catch agrupava `V2Exception`,
`InvalidArgumentException` e `TypeError` num único `404 Player not found`. Era tolerável enquanto
ninguém guardava a resposta; o CLS-2925 passa a gravá-la na activity do jogador, e o ticket da
activity diz que linha errada não tem reparação. Uma queda do Memberzone marcaria uma população
inteira como inelegível por um motivo que nunca foi verdade. A C dava ao caminho automático uma regra
mais estrita que o botão do operador; a F **não acrescenta regra**, corrige um rótulo já errado hoje
para todos os callers.

`V2Exception::getCode()` leva o status do upstream (`curl-library/GuzzleClient.php:141`), e ligação
sem resposta é reportada como 500 (`CurlClient.php:183`) — por isso o split funciona. Do lado deles
não é preciso nada: já tratam fora de `[400, 404]` como falha do lote, sem activity, marcando os
jogadores como não alcançados no step. **Não há reentrega** — o transporte é `max_retries: 0`.

## Achado para virar ticket próprio (2026-09-28)

**O celesta-promotion é o único serviço PHP da Celesta que não regista o
`SymfonyComponents\Subscriber\ErrorCodeResponseSubscriber`.** Doze registam-no, com o mesmo bloco de
quatro linhas em `config/services.yaml`; o promotion exclui todo o diretório `Subscriber/` do
autoload e regista à mão só o `KernelExceptionSubscriber`, o `FormResponseSubscriber` e o
`JsonRequestTransformerSubscriber`.

Consequência: os erros de validação do promotion saem como `{"message":"Validation Failed","errors":{…}}`
**sem `code`**, enquanto o `ValidationErrorsSchema` do próprio `src/Kernel.php` documenta o campo. A
documentação descreve algo que o serviço nunca emitiu.

Não corrigido no CLS-2923 de propósito: mudaria todas as respostas de erro do serviço, em endpoints
fora do ticket, e as recusas do endpoint já levam `code` porque são construídas à mão.

**Lição de método, minha, nesta sessão:** afirmei ao Lucas e escrevi numa mensagem para outra equipa
que o promotion devolvia `code: VALIDATION_CONSTRAINT`. Tirei isso do schema, não do comportamento.
Schema de OpenAPI não é evidência de comportamento — é exatamente o tipo de divergência que este
ticket existe para corrigir.

## Contrato acordado com o celesta-scenario (Pedro Martins, 2026-09-25)

- **Eles** geram a chave e mandam no payload. Formato `<scenarioId>:<ActionJob id>:<playerId>` — o id do job é
  `uniqid('job_')`, estável na reentrega, mas cobre lote de até 50 jogadores, então sem o `playerId`
  o segundo jogador do lote vira repetição do primeiro. **Confirmado no código** deles em 2026-09-25.
- `sourceUserId`: no chat ele disse `null` explícito, mas o **código omite o campo**
  (`PromotionClient::offerReward()` monta o body sem a chave). Os dois resolvem para `null` do nosso
  lado; a matriz segue o código, não o chat.
- **Dois desalinhamentos que são do lado deles**, levantados no review de 2026-09-25 e ainda por
  responder: o `getSkipReason()` lê `errors`, `error`, `title` e **nunca** `message` nem `code` — ou
  seja, as chaves legadas têm dois consumidores, não um; e `REFUSAL_STATUSES = [400, 404]` não
  inclui o 422, escrito contra a versão anterior do endpoint.
- O scenario chama o promotion **direto**, por host próprio com `guard_protected`, sem gateway. Hoje
  não tem `PromotionClient` — vão ter que criar, do lado deles.

## Pendente com a PO, não bloqueia o código

1. ~~Origem do bônus na lista do BO~~ — **resolvido em 2026-09-30**, virou a decisão H. Precisa dos
   três pedaços: promotion guarda e devolve (feito), o normalizer do BO repassa (branch criada,
   pendente), o front mostra a coluna (ticket de outro).
2. `offerKey` cobre reentrega do mesmo job, não disparo novo. Em config manual nada limita oferta
   repetida, porque `OccurrencesInRecurrencePeriodCondition` só roda em `automatic`.
3. Jogador que pediu para não receber oferta continua recebendo do cenário, igual à bulk action de
   hoje. Se o produto quiser a checagem, ela é do dono das regras da bulk action, para os dois
   caminhos de uma vez.

## Estado das outras branches do épico (lido em 2026-09-25)

Seis PRs abertos. Três não fazem o que o título sugere: **celesta-scenario `CLS-2924` é só a
validação ao gravar** (não oferta nada, não chama o nosso endpoint — a execução é o CLS-2925, ainda
em progresso) e **celesta-backoffice `CLS-2926` é só documentação OpenAPI**. constants
`CLS-412-CLS-2922` cria `ACTION_TYPE_OFFER_BONUS = 'offer_bonus'` (2 linhas); job-library
`CLS-412-CLS-2935` cria `EVENT_BONUS_OFFERED`/`EVENT_BONUS_OFFER_SKIPPED` (4 linhas); activity
`CLS-402-CLS-2934` aceita os dois eventos sem mascarar o payload, com testes de integração reais.

Contrato que já encaixa: nomes dos eventos idênticos entre PHP e Go; o GET de reward configuration
que o cenário faz ao gravar já devolve `type`, `status`, `offeringMethod`, `currency`, `reason` e
`model`. **Eles conseguem montar o payload inteiro da activity sem nós mexermos** — `bonus_id` sai
da nossa resposta da oferta, `type`/`reason`/`wager` saem desse GET (`wager` = `model`), `amount` e
`free_rounds` saem das opções do nó deles.

**Teste de integração real é possível**: `celesta-promotion` e `celesta-scenario` entram na rede
docker externa `celesta` com os aliases `promotionweb.docker` e `scenarioweb.docker`, e o
`.env.dev` do cenário já aponta `PROMOTION_HOST` para lá. Bloqueado até a execução deles existir.

Matriz de 23 células no spec, 14 delas A com critério observável. Célula 8 (duas chamadas
concorrentes com a mesma chave) fica sem teste automático de propósito — Behat é processo único e o
repo não tem harness de teste de controller.


## Achados de 2026-09-30

**`Bonus::jsonSerialize()` não é o que a lista de bônus devolve.** `GET /api/domain/{id}/bonuses`
passa por `BonusNormalizer::normalizeMany()` → `normalizeBonus()`, que monta o array dele. Campo
somado só na entity chega ao banco e para ali. Peguei isso no cruzamento doc × resposta real do
Newman, não lendo o código — foi o passo que o `ticket-postman` manda fazer e que teria passado batido.

**O `normalizeBonus()` não devolvia origem nenhuma**, nem `sourceUserId`. Somei os dois: expor só o
cenário deixaria a coluna de origem do BO capaz de nomear cenário e nunca operador. É mudança que o
ticket não pediu, registrada no spec como tal.

**O BO remapeia campo a campo, não repassa.** `GatewayBundle/Normalizer/Promotion/BonusNormalizer.php`
tem whitelist de 18 campos; o que não está nela some. É por isso que o item 2 das pendências existe.

**A `description` da action fica com o scenario.** O BO nunca mandou description para o promotion — a
bulk action manda só `amount`, `currency` e `sourceUserId` (`OfferFreeBonusHandler.php:80-82`), e a
descrição do modal vira `note` no `additionalData` da activity entry, com `sourceType = user`
(`UserActivityJobManager.php:155`). O scenario espelha: mesma activity, `sourceType = scenario`.

**Promotion não consegue saber quem está chamando.** `GUARD_KEY` é uma chave só para todo caller
(`config/parameters.yaml:12`), então "exigir `sourceUserId` se for BO, `sourceScenarioId` se for
scenario" não é implementável — só dá para confiar no que o caller declarar, que é igual a campo
opcional.

**Duas ofertas `offered` do mesmo par player × config não quebram o claim de depósito.**
`DepositRewardClaimService` recebe reward ids compostos `<rewardConfigurationId>:<bonusId>` e busca
aquele bônus com filtro de status (`resolveBonus()`); não tem "pega o primeiro" nem claim duplo. Logo
duplicação vinda de bug do scenario é problema deles, e visível, não silencioso.
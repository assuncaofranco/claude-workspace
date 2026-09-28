---
name: cls-412-cls-2923-decisions
description: "CLS-412-CLS-2923 (celesta-promotion, offer sem BO user e idempotente) — as 4 decisões de desenho, o contrato acordado com o time do celesta-scenario e as 3 perguntas pendentes para a PO"
metadata: 
  node_type: memory
  type: project
  originSessionId: 00170055-795b-4ad9-bb66-c5e084632793
  modified: 2026-09-28T08:38:12.786Z
---

Ticket filho do épico CLS-412 ("Offer bonus as a scenario action"). Estado em 2026-09-25: branch
`CLS-412-CLS-2923` criada a partir do master, **spec e plano escritos mas não commitados**, zero
código. Artefatos em `celesta-promotion/sdd/_specs/CLS-412-CLS-2923.md` e `sdd/_plans/`.

## As 4 decisões

| # | Decisão |
|---|---|
| A | `sourceUserId` vira opcional, `source_user_id` fica `NULL`. Nada de formato de cenário no bônus |
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

- **Eles** geram a chave e mandam no payload. Formato `<ActionJob id>:<playerId>` — o id do job é
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

1. O AC do pai diz *"its source identifies the scenario that created it"*, mas o filho manda não
   guardar nada de cenário no bônus. A lista de bônus do BO vai mostrar origem vazia; quem identifica
   o cenário é a activity do CLS-2925, que é outra tela.
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

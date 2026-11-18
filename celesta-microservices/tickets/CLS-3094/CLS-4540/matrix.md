# CLS-4540 — matriz (promotion, gift requests)

Pai CLS-3094. Código lido: `origin/CLS-4034` (promotion #586, ainda não mergeado), constants `dev-CLS-4032`.
Estado: **assinada pelo Lucas em 2026-11-05.** Nenhuma célula aberta.

## Decisões já tomadas

- Stock: não é critério. Request é outra entidade e nunca conta (Francisco, 2026-11-05).
- `quantity`: caiu do produto inteiro, não só do request. CLS-3247 OUT "Offering several gifts in one offer (quantity)", "One offer = one gift" (editado 2026-11-05 14:29); o plano do 4034 é de 23/10, anterior (Francisco, 2026-11-05). O 4540 não toca em `quantity`: se o 4034 mantiver o campo, o `GiftFactory` já cai no default 1.
- Stock: o CLS-3247 agora tem stock opcional na configuration, checado no offer (contagem de gifts × stock, sem corrida). O 4034 diz stock OUT: divergência do 4034 com o pai, não nossa. Para nós: nada a checar no 4540; o approve cria o gift pelo caminho do offer e herda o stock quando ele existir (caso 35).

## Dimensões

| # | Dimensão | Valores | Fonte |
|---|---|---|---|
| D1 | Ação | create, list por domínio, list por player, approve, reject | descrição do CLS-4540 (superfície nova, sem código ainda) |
| D2 | Status do request na ação | `requested`, `approved`, `rejected` | descrição do CLS-4540; constante ainda não existe (vai para `celesta-constants`) |
| D3 | Configuration no momento da ação | ok (gift, enabled), não existe / outra marca / apagada (Gedmo → null), tipo ≠ gift, `disabled` | `GiftRewardConfigurationConstraintValidator::validate()` (match em 3 ramos); `RewardConfiguration` `#[Gedmo\SoftDeleteable]` |
| D4 | Motivo (`reasonId`) | null, válido, não existe / outra marca / apagado | `GiftReasonConstraintValidator::validate()`; `RewardOfferingReason` `#[Gedmo\SoftDeleteable]` |
| D5 | Wallet do player | tem a moeda da configuration, não tem a moeda, player 404, wallet 5xx | `GiftController::postGift()` (catch `V2Exception` 404 / <500 / ≥500; `in_array` da moeda) |
| D6 | Valor | omitido (cai no `offerAmount` da configuration), informado | `GiftFactory::createFromRequestModel()` `$model->getAmount() ?? $configuration->getOfferAmount()` |
| D7 | Configuration mudou entre request e approve | nada, `offerAmount` mudou, `currency` mudou, ficou `disabled`, apagada | `GiftRewardConfigurationType` (PATCH aceita `currency`, `offerAmount`, `status`) + D3 |
| D8 | Motivo de rejeição | vazio / só espaço, informado | descrição do CLS-4540 ("reason mandatory") |
| D9 | Idade do rejeitado na lista do player | < 90 dias, exatamente 90, > 90 | descrição do CLS-4540 (fronteira numérica) |
| D10 | Origem do gift lido | veio de request aprovado, offer direto, gift anterior ao release | descrição do CLS-4540 ("none for direct or older gifts") |
| D11 | Concorrência | approve × approve, approve × reject no mesmo request | AC "exactly one gift" + "final states"; a idempotência do gift hoje é por chave do caller (`findOneByIdempotencyKey`), não protege isto |

Fora: `sourceScenarioId` (pai: request só vem do BO, cenário/promoção/bulk OUT), `quantity` (decidido acima).

## Casos

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 1 | create × config ok × motivo null × wallet ok × valor omitido | A | — | request `requested`, `requestedBy/At` preenchidos, valor = `offerAmount` da configuration; nenhum gift novo em `GET /gifts`; nenhum `GiftEventJob` |
| 2 | create × valor informado | A | ramo do `??` em D6 | request guarda o valor informado |
| 3 | create × motivo válido | A | — | request devolve `reasonId` / `reasonName` |
| 4 | create × motivo inexistente / outra marca / apagado | A | mesma regra do offer (400 em `reasonId`) | 400 com violação em `reasonId`, nenhum request |
| 5 | create × config inexistente / outra marca / apagada | A | — | 400 (ou 404, alinhar com o offer) e nenhum request |
| 6 | create × config tipo ≠ gift | E → 5 | mesmo `GiftRewardConfigurationConstraintValidator`, outra mensagem | — |
| 7 | create × config `disabled` | E → 5 | idem | — |
| 8 | create × player sem a moeda | A | mesma checagem do offer no create, menos stock (Lucas, 2026-11-05); o approve revalida | `CURRENCY_MISMATCH` 400, nenhum request |
| 9 | create × player 404 / wallet 5xx | A | idem 8 | 404 `PLAYER_NOT_FOUND` / 503 `UPSTREAM_UNAVAILABLE`, nenhum request |
| 10 | list domínio | A | — | só `requested` da marca, com player, configuration, valor, moeda, motivo, requestedBy/At; vazio = `[]` |
| 11 | list domínio × request de outra marca | A | isolamento por marca | não aparece |
| 12 | list player × `requested` | A | — | aparece |
| 13 | list player × `rejected` < 90d | A | — | aparece com motivo de rejeição, requestedBy/At, rejectedBy/At |
| 14 | list player × `rejected` = 90d | A | fronteira; inclusivo, `rejected_at >= agora − 90 dias` (Lucas, 2026-11-05) | rejeitado há exatamente 90 dias aparece; há 90 dias e 1 segundo não |
| 15 | list player × `rejected` > 90d | A | — | não aparece; a linha continua no banco |
| 16 | list player × `approved` | N | o pai mostra o aprovado como o gift dele, no History | — |
| 17 | approve × `requested` × config ok × wallet ok | A | — | um gift `claimed` com valor, moeda, configuration, motivo e descrição do request, quantity 1; request `approved` com `approvedBy/At` e link ao gift; um `GiftEventJob` CREATED |
| 18 | approve × `approved` | A | — | erro, nenhum gift novo |
| 19 | approve × `rejected` | A | — | erro, nenhum gift |
| 20 | reject × `requested` × motivo informado | A | — | request `rejected` com `rejectedBy/At` e motivo; nenhum gift; nenhum `GiftEventJob` |
| 21 | reject × motivo vazio / só espaço | A | — | 400, request continua `requested` |
| 22 | reject × `approved` | E → 18 | mesma guarda de estado final | — |
| 23 | reject × `rejected` | E → 18 | idem | — |
| 24 | approve × config mudou `offerAmount` | A | valor do request é o valor (Francisco, 2026-11-06: "fica com o valor que tem") | gift sai com o valor do request, não o `offerAmount` novo |
| 25 | approve × config mudou `currency` | A | approve sem impedimentos (Francisco, 2026-11-06); o `GiftFactory` hoje usa a moeda da configuration, então o approve não pode passar por ele como está | gift sai com a moeda do request |
| 26 | approve × config `disabled` / apagada | A | approve sem impedimentos: "a decisão é dele [...] não vamos implementar impedimentos, pelo menos para já" (Francisco, 2026-11-06). Apagada: `getRewardConfiguration` exclui pelo filtro do Gedmo, então o approve carrega com o filtro desligado | gift criado, ligado à configuration, request `approved` |
| 27 | approve × motivo apagado | A | idem 26; motivo carregado com o filtro desligado, como no CLS-4163 | gift criado com o `reasonId` do request |
| 28 | approve × player perdeu a moeda / 404 / wallet 5xx | E → 26 | sem checagem de moeda no approve, a wallet nem é chamada | — |
| 29 | approve × approve concorrente | A | — | exatamente um gift; o segundo recebe erro |
| 30 | approve × reject concorrente | E → 29 | mesma transição atômica a partir de `requested` | — |
| 31 | gift lido × veio de request | A | — | gift traz requester e approver (ids e datas) |
| 32 | gift lido × offer direto | A | — | requester e approver null, resto igual |
| 33 | gift lido × anterior ao release | E → 32 | sem link ao request, mesmo caminho | — |
| 34 | `GET /gifts/aggregate` com requests pendentes | A | pai: nada pendente chega a KPI | soma não muda depois de criar request |
| 35 | approve × stock da configuration esgotado | N | stock não existe no código (4034 diz OUT, nenhuma sub-task do CLS-3247 implementa). O approve cria o gift pelo mesmo caminho do offer, então quem implementar o stock cobre o approve ali (Lucas, 2026-11-06). Não perguntamos de novo ao Francisco | — |
| 36 | create × sem `requestedBy` | A | request só nasce no BO (pai: cenário, promoção e bulk OUT), então não existe a alternativa `sourceScenarioId` do offer (`Gift` model, `Assert\Expression`) | 400 em `requestedBy`, nenhum request |
| 37 | approve / reject × sem `approvedBy` / `rejectedBy` | E → 36 | mesma obrigatoriedade | — |
| 39 | approve × `sourceUserId` do gift criado | A | o offer exige `sourceUserId` ou `sourceScenarioId` (`Gift` model, `Assert\Expression`); aprovador, quem efetivamente ofereceu (Lucas, 2026-11-05) | gift aprovado tem `sourceUserId` = aprovador; o request guarda o requester |
| 38 | create × já existe request `requested` do mesmo player × configuration | N | o pai mede duplicado como indicador, não como bloqueio; o segundo é criado normalmente (Lucas, 2026-11-05; Francisco confirmou 2026-11-06) | — |

Caso 14 (90 dias inclusivo): Francisco, 2026-11-06, "é indiferente, pode aparecer".

## Onde cada critério entra

- **Pai CLS-3094: nada.** As respostas do Francisco (2026-11-06) são a leitura direta do pai ("with the requested values", sem impedimento escrito), então não há AC nova a escrever lá.
- **Plano do 4540**, só da promotion: `sourceUserId` = aprovador (39); update condicional (29, 30); create valida como o offer (8, 9); approve monta o gift com valor, moeda, configuration e motivo do request, sem revalidar e carregando apagados com o filtro do Gedmo desligado (24-28). Extrair o offer do controller **saiu**: o approve não revalida, só reaproveita o factory.
- **Split:** `quantity` ainda está em 4034, 4035 e 4037, e stock em nenhuma sub-task do CLS-3247. Vai para Francisco e Marcello, não para o autor do PR.

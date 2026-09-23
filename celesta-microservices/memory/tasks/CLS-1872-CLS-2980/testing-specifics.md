---
name: cls1872-testing-specifics
description: "CLS-1872 — tudo que é preciso para testar o épico à mão: tipos de gateway que pingam, chaves obrigatórias por tipo, perfis de permissão reais, gotchas de ambiente e sujeira deixada no banco"
metadata: 
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-22T14:03:28.553Z
---

# CLS-1872 — especificidades para testar

Reunido em 2026-09-22, depois do review do Fable e das correções. Complementa
`~/Desktop/celesta-projects/tickets/CLS-1872/` (epic.md, integration-test-plan.md, CLS-1872.md,
CLS-1872.postman_collection.json).

## 1. Qual tipo de gateway usar, e por quê

O validator do CLS-2979 resolve a chamada de leitura por um `match` no tipo, construído a partir dos
sincronizadores — **não** por `method_exists` no client (essa era a versão com bug, corrigida em
2026-09-22).

| Comportamento no save | Tipos | Chamada |
|---|---|---|
| **pinga o provedor de verdade** | betsoft, bongo, playn_go, pragmatic, redgenn, relax, wazdan, yggdrasil | `getGames()` |
| | quanta | `gamesList()` |
| | evolution | `getAvailableGamesList()` |
| | git_slot_park | `getGameList()` |
| | gamble_hub | `getCurrencies()` |
| | soft_gamings | `getGameFullListStream()` — baixa o catálogo inteiro, é pesado |
| **só checa as chaves** | aleaplay | `graphQlQuery(string $query)` exige argumento; deixado de fora de propósito |
| **rejeitado com 400** | aleaplay_v2, soft_gaming, absolute_live_gaming, bet_soft, reelsoft | a factory não implementa esses tipos |

**Para testar sem credencial real, use `gateway_type_aleaplay`.** É o único que atravessa a validação
inteira sem tocar a rede. Qualquer outro exige credencial que funcione, senão dá 400 — e isso é a
feature funcionando, não defeito.

**soft_gamings é o caro:** o `getGameFullListStream()` não é lazy — escreve o catálogo inteiro num
`php://temp` dentro do request. Por isso o BO manda `max_duration = CurlClient::EXTENDED_REQUEST_TIME_LIMIT`
(60s) nas duas chamadas de escrita; com o default de 25s o BO desistia, o game continuava, e o operador
via "falhou" numa conexão que tinha sido salva.

## 2. Chaves obrigatórias por tipo

Vêm de `GameGatewayClientFactory::getClient()` (celesta-game). Faltando qualquer uma que não tenha
`?? null`, a factory falha e o save é rejeitado com 400.

| Tipo | Chaves obrigatórias |
|---|---|
| aleaplay | `bonus_api_base_url`, `customer_api_base_url`, `environment_credential`, `secret_key` (+ `alea_casino_id` opcional) |
| playn_go | `free_game_url`, `free_game_wsdl_url`, `api_login`, `api_password`, `product_id` |
| git_slot_park | `base_url`, `api_token` |
| quanta | `api_url`, `username`, `password` (+ `launch_timeout_seconds` opcional) |
| betsoft | `base_url`, `bank_id`, `pass_key` |
| bongo | `game_list_url`, `access_token` |
| relax | `base_url`, `login`, `password` |
| redgenn | `base_url`, `login`, `password`, `wlCode` |
| yggdrasil | `game_list_url`, `free_round_url` |
| wazdan | `api_url`, `operator`, `license`, `hmac_secret_key`, `skin_id` |
| pragmatic | `base_url`, `game_list_path`, `game_launch_path`, `create_player_free_round_path`, `cancel_free_round_path`, `login`, `secret_key` (+ `launch_timeout_seconds`) |
| evolution | `licensee_hostname`, `casino_key`, `api_token`, `classification_api_token`, `state_api_token`, `reward_games_api_token` (+ `launch_timeout_seconds`) |
| soft_gamings | `domain`, `merchant_list_url`, `key`, `pwd`, `casino_server_ip` (+ `launch_timeout_seconds`) |
| gamble_hub | `office_api_url`, `client_api_url`, `login`, `password` (+ `game_api_url`, `secret_key`, `user_id` opcionais) |

## 3. Perfis de permissão que existem de verdade

**Local (fixtures):** só o `owner` tem as policies de integrations. `customer_support` não tem nenhuma —
serve para o caso "sem permissão → 403".

**preprod-1, company 1** (verificado no banco em 2026-09-21, fora o owner):

| Role | Access integrations | Update Game connections |
|---|---|---|
| `product_owner` (6666) | sim | **sim** |
| `head_of_operations` (3906) | sim | não |
| `acquisition manager` (3630) | sim | não |

Ou seja, em preprod o perfil "lê sem ver credencial" já existe. O que **não** existe é
*View Game connections only* — a policy `PS_GAME_CONNECTIONS_SEE` só passa a existir quando a
migration do CLS-2980 for deployada. Depois disso, criar um role com ela pela tela de Access control.

**Atenção:** esses roles são da company 1. O `preprod-test` usa o domínio 56 (madnix). Se a company do
domínio 56 for outra, confira os roles dela antes.

## 4. O que esperar em cada caso

| Quem chama | GET lista | POST / PUT |
|---|---|---|
| sem nenhuma das 3 permissões | 403 | 403 |
| `PS_INTEGRATIONS_READ` só | 200, **sem** a chave `options` | 403 |
| `PS_GAME_CONNECTIONS_SEE` só | 200, **sem** a chave `options` | 403 |
| `PS_GAME_CONNECTIONS_EDIT` | 200, `options` completo | 201 / 200 |

`options` é **omitido**, não mascarado. Não vem `null`, não vem `{}`, não vem `****`. A chave
simplesmente não existe no item — decisão do épico, seguindo CLS-2441 e divergindo do sportsbook
(CLS-1874, que mascara).

Campos graváveis: `name`, `enabled`, `options`, `freeRoundsCancelable`. O `type` só na criação — mandar
no PUT é rejeitado como campo extra. `enabled` e `freeRoundsCancelable` são **obrigatórios** no
payload: omitir dá 400, nunca é lido como `false`.

**`name` é único por domínio** (corrigido 2026-09-22, achado do Copilot). A tabela sempre teve o índice
único `(name, domain_id)`, mas as forms não estão ligadas à entidade, então o `#[UniqueEntity]` nunca
rodava e o nome repetido chegava ao flush como erro de driver — 500. Agora é 400 com o erro no campo
`name`. Ao testar: mesmo nome em **outro** domínio passa, e renomear uma conexão para o nome dela mesma
passa.

**Nome é único por marca, então a coleção usa `runTag`.** Cada execução do Newman monta os nomes com
os 6 últimos dígitos do relógio. Sem isso a segunda execução colide com a primeira e o passo 3 dá 400 —
legitimamente. Foi assim que a correção do nome duplicado apareceu na coleção.

**O erro de validação chega achatado no BO.** O game responde
`{"message": ..., "errors": {"enabled": [...]}, "code": ...}`; o `handleV2Exception` repassa só o mapa de
dentro, então o navegador recebe `{"enabled": [...], "code": "VALIDATION_CONSTRAINT"}` — nome de campo no
topo, sem `errors`, sem `message`. Verificado ao vivo em 2026-09-22. Importa para o CLS-2981.

Do lado do BO, o erro do game volta pelo `FormHelper::handleV2Exception`, que é compartilhado com todo
controller que faz proxy: **400 mantém o corpo de erro do game**, **404 mantém o status mas troca o
corpo** pelo genérico, e falha de transporte vira **500**. Não é "repassado igual" — a anotação, o spec
e o plano foram corrigidos para dizer isso.

## 5. Gotchas de ambiente

- **celesta-backoffice:** `make test` recria o banco de teste e **não** carrega fixtures. Todo teste
  funcional com token dá 401 até rodar
  `bin/console hautelook:fixtures:load --no-interaction --no-bundles --env=test`.
- **celesta-game:** precisa de um `.env` na raiz (é gitignored e nenhum script cria). `cp .env.dev .env`.
- **celesta-game:** ao acrescentar rota ou serviço, apagar `var/cache/test` e `var/cache/testDebug` à
  mão — `cache:clear --env=test` não cobre o cache que o phpunit usa.
- **Hook de commit:** rejeita a mensagem padrão de merge do git. Prefixar: `CLS-1872 Merge branch ...`.
- **MySQL normaliza a ordem das chaves em coluna JSON** (por tamanho, depois alfabética). Uma asserção
  com `assertSame` sobre `options` precisa da ordem que o banco devolve, não a que se digita.

## 6. Sujeira deixada no banco dev do game (domínio 1)

Não apagada, para você decidir:

- id 15 — `Review dup ...`, git_slot_park, habilitada, credencial falsa (do review do Fable)
- id 17 — `Review evo ...`, evolution, desabilitada (do review do Fable)
- várias linhas `Integration AleaPlay` / `Integration AleaPlay second` — cada execução do Newman cria
  duas. Inofensivas: as asserções comparam com uma contagem capturada na mesma execução.

## 7. Como rodar a coleção

```
newman run ~/Desktop/celesta-projects/tickets/CLS-1872/CLS-1872.postman_collection.json
```

Sem environment — ela traz os defaults de dev. Último resultado (2026-09-22, dev, os dois repos em
`CLS-1872-CLS-2979`): **19 requests, 44 assertions, 0 falhas**. Runbook em `CLS-1872.md`, ao lado.

Os passos 11-14 são os casos que as correções do segundo review criaram: nome duplicado, `enabled: null`,
os dois booleanos ausentes numa resposta só, e `options` vazio nunca voltando como `[]`.

**Para rodar em preprod:** basta trocar `BO_baseUrl`, as credenciais e o `domainId` — tudo passa pelo
Backoffice, nenhuma chamada interna, nenhum header de guard. Mas a migration do CLS-2980 precisa estar
deployada antes, senão o perfil *View Game connections only* não existe para testar.

Relacionado: [[cls1872-cls2980-findings]], [[preprod-db-read]].

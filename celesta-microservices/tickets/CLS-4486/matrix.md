# CLS-4486 — matriz (game, pai CLS-3063)

Levantada em 2026-11-03 sobre `celesta-game` master `3199ce373`, revisada no mesmo dia (Fable, depois Opus).
Toda célula cita arquivo e linha. Caminhos de `src/` abreviados: `XProvider` = `src/AppBundle/Provider/XProvider.php`,
`X/Handler` = `src/XBundle/Handler/`.

## O problema em uma frase

O game user é uma linha por jogador × moeda × país do IP (`UserRepository::getOrCreate:35-58`). Cada provider
recebe uma coluna dessa linha como id do jogador. CGA, Play'n GO e GambleHub recebem `user_id` (a conta), que
**se repete** entre as linhas do mesmo jogador; com multi wallet o provider vê um jogador só em duas moedas.
O ticket dá a cada linha nova um `game_user_id = PID<user_id>GUID<id>` e faz todo provider receber esse valor.

## Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| Provider | 14 com cliente: AleaPlay, Betsoft, Bongo, Evolution, GambleHub, GitSlotPark, PlaynGo, Pragmatic, Quanta (CGA), Redgenn, Relax, SoftGamings, Wazdan, Yggdrasil. Os outros 5 de `TYPES` não têm cliente | `GameGatewayClientFactory.php:49-157` (switch, cai em `CLIENT_NOT_IMPLEMENTED`) |
| Provider em uso | 8: CGA, GitSlotPark, GambleHub, SoftGamings, Evolution, Redgenn, Betsoft, Relax | lista do PO, 2026-09-29; Yggdrasil chega pela CGA |
| Game user | novo, com `game_user_id` / antigo, NULL | sub-task |
| Chave na criação | desligada / ligada | sub-task (`GAME_USER_ID_GENERATION_ENABLED`, variável de ambiente do Team O) |
| Resolução do game user no lançamento | reaproveita (mesma moeda + país) / cria linha / falha ao gravar | `UserRepository::getOrCreate:48-57` |
| Onde o id viaja | lançamento / resposta de callback / busca da sessão no callback / comparação no callback / concessão de free round / cancelamento de free round | tabela abaixo |
| Modo | real / demo | `GameController.php:235-239` |

## Onde cada provider usa o id do jogador hoje

Valor de hoje: **U** = `user_id` (conta, repete entre moedas), **I** = `id` da linha, **I4** = `id` com zero à
esquerda até 4 dígitos. "—" = o provider não usa o id naquele ponto.

| Provider | Hoje | Lançamento | Resposta de callback | Busca da sessão no callback | Comparação no callback | Free round: concede / cancela |
|---|---|---|---|---|---|---|
| Quanta (CGA) | U | `QuantaProvider:125` | `Quanta/Handler/AuthenticateHandler:64` | token (`Quanta/Handler/AbstractHandler:120-125`) | — | `QuantaProvider:179` / — |
| PlaynGo | U | — | `PlaynGo/Handler/AuthenticateHandler:52` (`externalId`) | token (`PlaynGoProvider:95`) | — | `PlaynGo/Normalizer/GrantFreeRoundNormalizer:30` / — |
| GambleHub | U | `GambleHubProvider:75` (`player_login`) | — | id de sessão do provider (`GambleHub/Handler/AbstractHandler:47-49`) | — | sem free round |
| GitSlotPark | I4 | `GitSlotParkProvider:74-77` | — | **id do jogador**: `ltrim` dos zeros → `getLastGameSessionByGameAndUser(int)` (`GitSlotPark/Handler/AbstractHandler:46-50`, `GitSlotParkProvider:182`) | — | sem free round |
| Evolution | I | `EvolutionProvider:172` | — | token (`EvolutionProvider:258`) | `!= $user->getId()`: Balance:51, Debit:61, Credit:60, Check:43, Cancel:140, PromoPayout:280 | `EvolutionProvider:380,456` / — |
| AleaPlay | I | `AleaPlayProvider:127-128` (id entra na assinatura) | — | token (`AleaPlayProvider:234`) | `GetBalanceHandler:77`; `AbstractTransactionHandler:32` com `intval()` | `AleaPlayProvider:175` / — |
| Betsoft | I | — | `Betsoft/Handler/AuthenticateHandler:104` | **id do jogador**, todo callback menos authenticate: `Betsoft/Handler/AbstractHandler:113-118` → `BetsoftProvider:212-213` → `getGameSessionByUser(int)` | — | `BetsoftProvider:149` / — |
| Bongo | I | — | `Bongo/Handler/LoginHandler:54` | token (`Bongo/Handler/AbstractHandler:86-98`) | — | sem free round |
| Pragmatic | I | — | `Pragmatic/Handler/Auth:60` | token (`PragmaticProvider:252`) | — | `PragmaticProvider:156` / — |
| Redgenn | I | — | `EnterHandler:92`, `ReEnterHandler:92` (`wlid`) | token ou id de jogo do provider (`RedgennProvider:223-225`) | — | `RedgennProvider:149,163` / — |
| Relax | I | — | `Relax/Handler/VerifyTokenHandler:56` (`customerid`) | token (`RelaxProvider:241`) | — | `RelaxProvider:180` / — |
| SoftGamings | I | `SoftGamingsProvider:147-148` (`Login`, senha = `md5(Login)`), `:424` | — | token (`SoftGamingsProvider:94`) | — | `SoftGamingsProvider:239,245-248` / `:215` |
| Wazdan | I | — | `Wazdan/Handler/AuthenticateHandler:105` | token (`WazdanProvider:248`) | — | `WazdanProvider:173` / `:201`, ou `findOneBy(userId)` em `:206` |
| Yggdrasil | I | — | PlayerInfo:53, GetBalance:53, Wager:120,223, EndWager:116, CampaignPayout:106,135 | token, ou **id do jogador** quando não vem token, nos dois ramos: com `gameId` (`getLastGameSessionByGameAndUser(int)`) e com `transactionId` (`getGameSessionByProviderTransactionId(string, int $playerId)`, `GameSessionRepository:251-259`) — `Yggdrasil/Handler/BaseGameSessionAbstract:36-46` → `YggdrasilProvider:84-88`; resposta de erro busca pelo id (`YggdrasilProvider:273`) | — | `YggdrasilProvider:247` / `:176` usa a conta (bug anterior) |

A concessão de free round acontece **dentro do lançamento**, com o mesmo game user da sessão
(`GameLaunchManager::grantFreeRounds:82,95`). O game user só nasce em `GameLaunchManager:132`.

## Casos

Classes: **A** afetado (tem que ser exercitado), **N** não afetado (com o ramo que exclui), **E → n** mesmo
caminho de código que o caso n.

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 1 | chave ligada × jogador sem game user × real | A | — | dado um jogador sem game user e a chave ligada, quando lança, então a linha nova tem `game_user_id = PID<user_id>GUID<id>` e o provider recebe esse valor |
| 2 | chave desligada × jogador sem game user | A | — | dado a chave desligada, quando lança, então a linha nova tem `game_user_id` NULL e o provider recebe o valor de hoje |
| 3 | chave ligada × linha antiga (NULL) na mesma moeda + país | A | — | reaproveita a linha, `game_user_id` continua NULL, o provider recebe o valor de hoje |
| 4 | linha com `game_user_id` × relançamento na mesma moeda + país | A | — | reaproveita a linha e manda o mesmo `game_user_id` |
| 5 | chave desligada × linha que já tem `game_user_id` | A | — | o provider continua recebendo o `game_user_id`; desligar a chave não troca id já dado |
| 6 | chave ligada × moeda ou país novo | E → 1 | mesmo `getOrCreate:57` → `save`, sem match | — |
| 7 | chave ligada × falha ao gravar (inclui choque no índice único) | A | — | nenhum game user criado, lançamento devolve erro, nenhum id antigo enviado |
| 8 | coluna ainda não existe | N | deploy em duas etapas, migration antes do código (D4) | — |
| 9 | demo | N | só o modo real cria sessão e game user (`GameController.php:235-239`) | — |
| 10 | sessão criada dentro de callback (Quanta `AbstractHandler:502`, SoftGamings `:340`, Evolution, AleaPlay, Pragmatic) | N | reaproveita o user da sessão existente; game user só nasce em `GameLaunchManager:132` | — |
| 11 | game user novo × cada provider × lançamento e resposta de callback | A (14) | cada provider tem suas próprias linhas (tabela acima) | o lançamento e as respostas de callback levam `PID…GUID…` |
| 12 | game user antigo × cada provider | A (14) | fallback é por provider (U, I, I4), linha a linha; erro num não aparece no teste de outro | o provider recebe exatamente o valor de hoje |
| 13 | game user novo × busca da sessão pelo id × Betsoft, GitSlotPark, Yggdrasil | A | buscam a sessão pelo id recebido em repositório tipado `int` (tabela acima); `PID…GUID…` quebraria a busca | dado um game user novo, quando o provider chama aposta e ganho com `PID…GUID…`, então a sessão certa é encontrada e liquida no game user certo |
| 14 | game user antigo × busca da sessão pelo id × Betsoft, GitSlotPark, Yggdrasil | A | mesmo ponto do 13, ramo do id antigo (GitSlotPark tira os zeros) | com id antigo, a busca funciona como hoje |
| 15 | busca da sessão × os outros 11 | N | token ou id de sessão/jogo do provider, sem id do jogador (tabela acima) | — |
| 16 | game user novo × comparação × AleaPlay | A | `intval('PID…')` = 0, rejeitaria sempre (`AbstractTransactionHandler:32`, `GetBalanceHandler:77`) | callbacks da AleaPlay com id novo são aceitos |
| 17 | game user novo × comparação × Evolution | A | 6 comparações com `getId()` | callbacks da Evolution com id novo são aceitos |
| 18 | game user novo × resposta de erro × Yggdrasil | A | `findOneBy(['id' => 'PID…'])` volta null e quebra (`YggdrasilProvider:273`) | resposta de erro devolvida sem exceção |
| 19 | game user novo × concessão de free round × 11 providers | A | concedida no lançamento com o mesmo game user (`GameLaunchManager:95`) | a concessão leva o mesmo id do lançamento |
| 20 | game user novo × cancelamento de free round × SoftGamings, Wazdan, Yggdrasil | A | os únicos cancelamentos que mandam id do jogador (tabela acima) | o cancelamento leva o mesmo id da concessão |
| 21 | 5 tipos sem cliente | N | `GameGatewayClientFactory` lança `CLIENT_NOT_IMPLEMENTED` antes de qualquer id | — |
| 22 | chamadas internas com `user_id`: wallet (ex. `Quanta/Handler/DebitHandler:177`), CRM (`Betsoft/Handler/GetAccountHandler:106`), free round grants (`BonusWinHandler:149`, `GameLaunchManager:86`) | N | não vão ao provider; wallet, CRM e grants são por conta. **Ficam `user_id`** | — |
| 23 | `testaccount` da CGA (`QuantaProvider:127`, `Quanta/Handler/AuthenticateHandler:70`) | N | compara `user_id` com a lista `test_accounts` da configuração, que é de contas. **Fica `user_id`** | — |
| 24 | `user_id` do merchant na GambleHub (`GambleHubProvider:87`, `$client->getUserId()`) | N | credencial do gateway, não é o jogador. **Não muda** | — |
| 25 | `user_id` em logs (ex. `AleaPlay/Handler/AbstractHandler:164`) | N | só log | — |
| 26 | callbacks do game-go | N | CLS-4487 (PR game-go#118) | — |
| 27 | `GameUserController` (`/user/{id}`, `/user/{id}/info`) e `User::jsonSerialize` | N | não expõem `game_user_id`: pai OUT "showing the id anywhere other than BRH"; BRH é CLS-4491 via BigQuery | — |

## Decisões

| # | Pergunta | Decisão e motivo | Quem |
|---|---|---|---|
| D1 | Backfill dos game users antigos? (pai, linha aninhada no Scope IN, × sub-task "no backfill") | Não. A linha serve todos os providers, que leem colunas diferentes dela; um valor por linha quebraria CGA (se `id`) ou os outros (se `user_id`), e `user_id` repetido viola o índice único. Bate com o OUT do pai | Lucas |
| D2 | Free rounds, que a sub-task não cita? | Entram. A concessão é parte do lançamento (`GameLaunchManager:95`); com ids diferentes o provider dá as rodadas a um jogador que nunca entra. Nenhuma outra sub-task cobre | Lucas |
| D3 | Testes nos 14 bundles? | Código nos 14, como a sub-task pede; unitário nos 14; coleção e preprod nos 8 em uso. O bug antigo do cancelamento da Yggdrasil (conta × linha) fica fora | Lucas, com a lista do PO |
| D4 | "Tolerate the column not existing"? | Não implementar no PHP: a coluna fica mapeada no Doctrine e, se faltar, quebra toda leitura de game user. Deploy em duas etapas: PR só com a migration, deployado e concluído antes do código. Necessário porque os 3 workers SQS e os 10 cronjobs do game sobem sem esperar a migration em prod-1 (preprods e staging-1 migram num Job PreSync desde CEL-9673, 2026-11-03) | Lucas |
| D5 | Callback resolve o game user pelo `game_user_id` no PHP? | Sim, onde a sessão é buscada pelo id do jogador: Betsoft, GitSlotPark, Yggdrasil (casos 13, 14). Id no formato novo (`^PID[0-9]+GUID[0-9]+$`, o mesmo do game-go) busca por `game_user_id`; senão, o caminho de hoje. Os outros 11 buscam por token e não mudam a busca. Ids antigos são só número e nunca casam com o formato novo, então não há ambiguidade. Primeira versão desta decisão dizia "só token" e estava errada (revista 2026-11-03) | Lucas, 2026-11-03 |

## Pendente

- **Regras de id de cada provider** (critério do pai): Francisco vai mandar a doc. Só a da GitSlotPark está no
  ticket (alfanumérico, 4 a 48).
- **Pedido ao Team O** (variável): status desconhecido; bloqueia o deploy, não o plano.
- **Compendium §2.2:** doc do Notion, não é nosso; vai nas instruções de deploy com o formato novo, para o TL.

## Notas para o plano e o teste

- A geração precisa do `id` da linha, que só existe depois do INSERT: dentro do `wrapInTransaction` do
  `getOrCreate`, inserir → ler `id` → gravar `game_user_id` → flush. Falha em qualquer ponto desfaz a linha (caso 7).
- Resolver pelo id novo é **busca pela coluna** `game_user_id`, não extrair o `GUID<id>` da string: é o que o
  game-go faz (`GetInternalUserIDByGameUserID`, paridade exigida pelo pai) e não aceita um id forjado
  (`PID1GUID1234` acharia a linha 1234 sem existir esse id).
- SoftGamings: a senha deriva do login (`md5(Login)`, `:148`); com login novo, a senha segue. Na concessão
  (`:245-248`) usar a mesma regra.
- Jogador que já tentou lançar em outra moeda antes do release tem linha antiga (NULL) nessa moeda, criada
  mesmo com o lançamento falhando (`GameController.php:236` cria antes do `launchGame` da `:241`). Continua
  quebrado, como diz o OUT do pai. Em preprod, usar jogador que nunca lançou na moeda nova.
- Redgenn está em uso mas fora do "Verified on" do pai: entra nos testes de plataforma.
- Antes do preprod, confirmar se os callbacks da GitSlotPark caem no PHP ou no game-go (o PR game-go#118 mexe
  no handler dela), para a coleção exercitar o caminho ativo. O código do PHP muda de qualquer jeito (D3).
- qaa-mock só simula serviços da Celesta, não providers: nada a mudar.

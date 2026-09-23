# Postman — referência Celesta

O que a skill genérica `ticket-postman` deixa de fora por ser específico daqui. Endpoints, portas e
convenções de path estão em [`context.yaml`](context.yaml); credenciais em `~/.claude-secrets/`
(`celesta-dev.md` para local, `celesta-preprod.md` para pp1).

## Variáveis — espelhar as environments do time

Usar os **mesmos nomes** que os arquivos de environment do time já definem, para que uma environment
por estágio sobrescreva os defaults de dev e o PO só troque de environment. Backoffice usa nomes com
prefixo `BO_`; o Gateway usa sem prefixo.

| Serviço | Var de base url | Dev | Host interno |
|---|---|---|---|
| Gateway (player) | `{{baseUrl}}` | `http://localhost:93` | `gatewayweb.docker` |
| Backoffice (admin) | `{{BO_baseUrl}}` | `http://localhost:84` | `backofficeweb.docker` |
| Wallet (DEV-ONLY) | `{{walletUrl}}` | `http://localhost:88` | `walletweb.docker` |
| Promotion (DEV-ONLY) | `{{promotionUrl}}` | `http://localhost:99` | `promotionweb.docker` |
| Game (DEV-ONLY) | `{{gameUrl}}` | `http://localhost:89` | `gameweb.docker` |

Credenciais seguem o mesmo corte — Backoffice: `{{BO_oauth_client_id}}`, `{{BO_oauth_client_secret}}`,
`{{BO_username}}`, `{{BO_password}}`, token → `BO_access_token`. Gateway: `{{oauth_client_id}}`,
`{{oauth_client_secret}}`, `{{username}}`, `{{password}}`, token → `access_token`. **Os valores não
ficam na coleção** — entram na environment do runner, vindos do vault, em tempo de execução.

## Auth — `POST /oauth/2.0/token`

A rota é `oauth/2.0/token` nos dois. `oauth/token` é o erro que já custou uma sessão.

**Backoffice** — campos **flat**. Qualquer campo extra ou aninhado (`deviceInformation`) leva a
400 `"This form should not contain extra fields"`:

```json
{ "grant_type": "password", "client_id": "{{BO_oauth_client_id}}",
  "client_secret": "{{BO_oauth_client_secret}}",
  "username": "{{BO_username}}", "password": "{{BO_password}}" }
```

**Gateway** — `deviceInformation` **é** obrigatório aqui:

```json
{ "grant_type": "player", "username": "{{username}}", "password": "{{password}}",
  "client_id": "{{oauth_client_id}}", "client_secret": "{{oauth_client_secret}}",
  "deviceInformation": { "ip": "127.0.0.1", "userAgent": "Mozilla/5.0" } }
```

E-mail de player vive na member-zone, fora destes repositórios — o username do gateway tem que ser
confirmado e bater com o `playerId`/`walletOwnerId` usado no resto da coleção.

## Convenção de path

- **Gateway (player):** sem `domainId`/`playerId` na URL — os dois vêm do token. Paths na raiz
  (`POST /reward/bonuses/claim`).
- **Backoffice (admin):** prefixo explícito `/api/gateway/domain/{domainId}/...`.
- **Interno (wallet/promotion/game):** `/api/domain/{domainId}/...` — **evitar** (regra de ouro).
  Protegido por guard em dev, então chamada direta precisa do header assinado.

## Guard — DEV-ONLY

O esquema do HMAC e o script de pre-request estão em `~/.claude-secrets/celesta-dev.md`, porque a
chave anda junto. Resumo: header `x-guard-secret`, HMAC-SHA256 sobre método + host (sem porta) +
path decodificado, mais o md5 do body em POST/PUT/PATCH.

O script lê a chave de `pm.environment.get('guardKey')`, não literal — para que a coleção versionada
não carregue o valor.

## Geração do spec

Nenhum serviço Celesta versiona `public/open-api.json`. Gerar antes de montar a coleção:

```bash
make openapi
# ou, direto:
docker exec <service>.php bin/openapi \
  --processor SymfonyComponents\\OpenApi\\Processor\\SchemaQueryParameter \
  --version 3.1.0 -o public/open-api.json --format json src
```

## Cadeia de referência — fluxo de reward / free rounds

O exemplo canônico. Para um ticket que não é de reward, montar a cadeia análoga a partir do spec do
próprio ticket e do `open-api.json` do serviço.

| # | Entrada | Método + path | Body / observação |
|---|---|---|---|
| 1 | BO | `POST {{BO_baseUrl}}/api/gateway/domain/{{domainId}}/reward-configuration` | Body verificado: `{ name, displayName, type:"free_rounds", model:"winnings", offeringMethod:"manual", currency, validDuringDays, claimingEvent:"direct", offerValidFor, freeRoundConfiguration:{ freeRoundsGameGateway, freeRoundsGameStudio, gameIds:[{id}], amount } }`. Os campos de free round vão **aninhados** em `freeRoundConfiguration`; `freeRoundsGameGateway`/`Studio` são o `game_gateway_configuration_id`/`game_studio_id` do jogo. Captura `.id` → `rewardConfigId`. **Não** precisa de promotion-configuration. |
| 2 | BO | `PATCH .../reward-configuration/{{rewardConfigId}}` | `{ "status": "enabled" }` — nasce `disabled`; sem habilitar, o offer dá 400 `"Reward configuration is disabled"`. |
| 3 | BO | `POST .../reward/bonus/{{rewardConfigId}}/offer` | `RewardFreeRoundsOfferRequest` = `{ playerId, freeRoundsRoundCount, message }` → status `offered`. |
| 4 | GW | `GET {{baseUrl}}/reward/bonuses` depois `POST {{baseUrl}}/reward/bonuses/claim` | O LIST captura `claimRewardId` (id composto do último reward oferecido) e `bonusId` (o sufixo numérico `_rewardId` = o `bonus_id` da wallet); o CLAIM usa `rewardIds: ["{{claimRewardId}}"]`. **Capturar no LIST**, do lado do player — montar o composto a partir de vars do lado do Backoffice falha entre ambientes. O claim **já** concede a free round (Promotion→Game); não existe passo manual de grant. |
| 5 | Wallet (DEV-ONLY) | `POST {{walletUrl}}/api/domain/{{domainId}}/wallet/{{walletOwnerId}}/game-transaction/all` | `type=bonus_deposit`, `subBalance = {{bonusId}}` — o id **numérico** do bonus no Promotion (capturado do `.id` da resposta do OFFER, **não** do composto do claim). Em preprod quem dirige isso é o provedor do jogo. |

## Armadilhas já pagas

- **Triple consistente:** `gameId` + seu `game_gateway_configuration_id` + `game_studio_id` têm que
  vir do **mesmo** jogo de free round. Conjunto inconsistente devolve `"invalid choice"` ou
  `"extra fields"`.
- **Usuários seeded** têm senha única e contas fixas de BO — ver `celesta-dev.md` no vault.
- O claim do player já concede a free round. Um passo manual de grant é sinal de que a cadeia está
  errada, não de que falta um passo.

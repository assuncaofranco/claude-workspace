---
name: project_cls1186_preprod_newman
description: "Como testar preprod-1 com Newman pelo Backoffice — rota de token correta, descoberta de domínio, e o domínio 213 (Sportsbook)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a6c580fa-781f-42c7-a3ed-acf00d5bae40
  modified: 2026-09-16T14:09:17.185Z
---

Aprendido testando o `potentialWinnings` do CLS-1186 em 2026-09-16 (ver [[project_cls1186_master_merge]]).

## Correções ao skill `preprod-test`

O skill documenta o token do Backoffice em `POST {{BO_baseUrl}}/oauth/token`. **Está errado** — dá 404 com HTML. A rota real é:

```
POST https://backend-api.preprod-1.octopodev.com/oauth/2.0/token
```

(`src/OAuth2Bundle/Controller/TokenController.php`, `#[Route('oauth/2.0/token')]`). Corpo JSON igual ao documentado; token vale 900s.

O skill também diz "PP1, domain 56" como default. **56 é a madnix**, casino. Player de sportsbook não está lá.

## Descobrir o domínio de um player sem pedir pro Lucas

```
GET /api/gateway/domains          → lista todos (140 em PP1; filtre status=active)
GET /api/gateway/domain/{d}/player/{playerId}   → 404 se não for o domínio certo
```

Domínios ativos úteis em PP1: **56 madnix**, 120 Winoui, 174 Celesta, 212 Celesta.io [DO NOT MODIFY], **213 Sportsbook**, 215 Vibrez! (Paul test). As mesmas credenciais `celesta-dev@lancaster-solutions.com` enxergam todos — não precisa de credencial por marca só para **ler**.

## Rotas de BO úteis

| o que | rota |
|---|---|
| apostas do player | `GET /api/gateway/domain/{d}/player/{p}/bets?limit=50&offset=0` → `{data: [...], total: n}` |
| transaction report | `POST /api/gateway/domain/{d}/finance/transaction_reports` |
| player | `GET /api/gateway/domain/{d}/player/{p}` |

O `/bets` do BO é **pass-through puro** do celesta-sportsbetting (`json_decode(sportsbettingClient->getPlayerBets())`), então testar por ele mede promotion → SB → BO de ponta a ponta.

## Armadilha de nome no payload de bet

Existem dois `potentialWinnings` em níveis diferentes:
- `bet.potentialWinnings` → **string** (`"10.80"`), ganho potencial da aposta (stake × odds). Pré-existente ao CLS-375, nada a ver com promoção.
- `bet.rewarding[].potentialWinnings` → **objeto** `{real, bonus}`, o do CLS-1186.

Quem olhar o primeiro conclui "não está retornando objeto" com tudo funcionando.

## Onde fica a collection

`~/Desktop/celesta-projects/_local-postman-collections/CLS-1186-preprod-potential-winnings/` (`chmod 600`). Credenciais de preprod **nunca** num repo de serviço — ver [[feedback_local_postman_collections_folder]]. Newman em `~/.npm-global/bin/newman` (não está no PATH).

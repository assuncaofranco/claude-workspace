# CLS-1283 flipper smoke

**Feature:** wallet, backoffice, gateway e cms-v2 sobem e respondem sem o Flipper (CLS-3150, 3904, 3905, 3906).

## Setup
- Stack local de pé: gateway, backoffice, wallet, cms-v2 (`strapi-madnix`).
- Cada serviço na branch que se quer testar (master para a linha de base, `CLS-<n>` depois).
- `./run.sh` (credenciais vêm do vault na hora).

## Steps
1. Rodar com `FLIPPER_DATABASE_URL` no env de cada serviço.
2. Tirar `FLIPPER_DATABASE_URL`, recriar os containers, rodar de novo.

## Variables
| Variable | Example | What it is |
|---|---|---|
| `baseUrl` | `http://localhost:93` | gateway |
| `BO_baseUrl` | `http://localhost:84` | backoffice |
| `cmsV2Url` | `http://localhost:3030` | cms-v2 |
| `domainId` | `1` | domínio |
| `playerId` | `1` | player do BO |

Capturados em runtime: `access_token`, `BO_access_token`.

## Notes
- Folder 1: gateway `/ping` (exige token) + `/wallet/balances` (gateway → wallet).
- Folder 2: BO `/player/{id}/wallets` (BO → wallet). Não usar `/wallet/transactions`: lê do BigQuery, e o `BIGQUERY_KEY` local é inválido (500 sem relação com o ticket).
- Folder 3: cms-v2 `/_health`, DEV-ONLY. Nenhum content type usa o bonus-list-picker, então não há leitura de conteúdo para fazer.
- Linha de base 2026-10-21: 6/6 verde, com a wallet local na branch `CLS-1283-CLS-2485`.
- Branches `CLS-3150/3904/3905/3906` 2026-10-21: 7/7 com a env (BO, cms-v2) e 7/7 sem a env nos quatro containers.
- Sem a env no cms-v2 = tirar a linha do `api/.env` local e recriar o `strapi-madnix`.
- Preprod: trocar as URLs e o `playerId`; o folder 3 não roda lá.

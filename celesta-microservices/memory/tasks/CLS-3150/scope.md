---
name: cls3150-scope
description: "CLS-1283-CLS-3150 (remove remaining flags/migration code) — escopo fechado 2026-10-20: remover o Flipper inteiro de wallet, backoffice e gateway; promotion e game já limpos"
metadata:
  node_type: memory
  type: project
  originSessionId: 7c16fbf2-1a26-475a-8ca1-a2bb9c56e895
  modified: 2026-10-21T10:15:17.001Z
---

Sub-task sem descrição do CLS-1283 (épico CLS-1277), atribuída ao Lucas. As irmãs (1624, 2485, 2759,
3147, 3707, 3708, 3833, 850) já cobrem controllers, jobs, listeners, guards e o rename `old_`.

**Decisão (2026-10-20, Lucas + Marcello):** remover o Flipper **inteiro** dos nossos MS, sem rastro.
Primeiro o Lucas queria manter o client e tirar só as flags; mudou depois que o Marcello confirmou que
apagou o client da promotion de propósito (CLS-2852, `b0712a91f`): "se precisarmos um dia, recriamos".
O game também já apagou o dele (CLS-2851, `c0b78d713`).

A única flag que esses 5 serviços chegaram a ler foi `move_bonus_to_promotion`, e todas as leituras já saíram.

## Entra (só código)

- wallet, backoffice e gateway: `src/Library/FlipperClient.php` + teste, o service em `services.yaml`,
  `flipper_database_url` em `parameters.yaml`, `FLIPPER_DATABASE_URL` nos `.env*`.
- No gateway, também: `tests/Mock/FlipperClient.php`, `FlipperClientStub.php`, o override em
  `services_test.yaml` e a referência em `WorkerStateIsolationTest`.
- Por que BO e gateway entram, mesmo não sendo nossos (ver [[our-services]]): o Flipper foi colocado
  neles pelo nosso épico e só para `move_bonus_to_promotion`. No gateway foi o CEL-6898 (`18bad18b7`, o
  próprio Lucas), no BO o CLS-392-CLS-1297 (`43b8c3e8ba`) e na wallet o CLS-392-CLS-1284 (`914a77d82`).
  Nenhum deles leu outra flag.
- cms-v2 (adicionado 2026-10-20): plugin `api/src/plugins/flipper`, `config/flipper.ts`, o registro em
  `plugins.ts`, `FLIPPER_DATABASE_URL` no `.env.example`, os testes do plugin, a entrada no `package-lock`
  e o teste do `bonusListResolver` que afirma "never consults the flipper plugin". A única flag que o
  cms-v2 já leu foi `move_bonus_to_promotion`, removida no CLS-2850 (`7814ff8`).
- cms e contact: nada (só `feature_flags` no `service-boundary.yaml`).
- promotion e game: só confirmar que estão limpos (no master de 2026-10-20 estavam).

## Fora

- Argocd (env `FLIPPER_DATABASE_URL`) e o registro da flag na tabela `flips`/`flip_actors`: não é
  nosso código. No máximo vira nota no DI.
- celesta-scripts (CEL-6848, CLS-1069, CLS-2074): scripts de execução única, com cópia própria do client.
- O sistema Flipper continua vivo em backoffice-front e sportsbetting (outros times), e o banco dele fica.
  O cms-v2 é nosso e o plugin dele **sai** (CLS-3906).

## SDD: modo mesclado (2026-10-20)

Usar o plugin novo onde der (`sdd-plan`, `sdd-implement`) e cobrir o resto pelo fluxo antigo, enquanto
o time não se adequa. Faltam dois ajustes: uma linha sobre o Flipper na spec do CLS-1283 (pai do
Marcello) e uma sub-task por repo (3150 = wallet + duas irmãs novas para BO e gateway).
Escrita no Jira só com confirmação do Lucas.

**Feito em 2026-10-20:** spec do CLS-1283 com os acréscimos do Flipper (escopo, fora, 4 critérios,
superfícies). Sub-tasks: CLS-3150 = `[wallet]`, CLS-3904 `[backoffice]`, CLS-3905 `[gateway]`,
CLS-3906 `[cms-v2]`, todas D-Team e com repo; as três novas sem assignee. O Rasoul já foi avisado
pelo Lucas de que o "FlipperClient stays" da CLS-3707 mudou. **2026-10-20 ~15:55: os 4 planos estão escritos no Jira** (label `sdd-plan`), cada um numa sessão própria;
a coordenação fica numa sessão separada. Branch = chave pura (`CLS-3150`, `CLS-3904`, `CLS-3905`, `CLS-3906`), a partir
do master. Próximo: montar a coleção de smoke em `tickets/CLS-1283/` (os 4 planos citam), depois
`/sdd-implement` em cada sessão, com `/clear` antes. O plano descreve
as checagens de smoke (boot + uma rota por serviço, com e sem a env), **sem citar a coleção**: a coleção é
ferramenta nossa (`tickets/CLS-1283/flipper-smoke/`), e o Jira é do time (Lucas, 2026-10-20: "não podemos confundir").

**Plano do CLS-3150 (wallet) escrito no Jira em 2026-10-20**, label `sdd-plan`. Branch `CLS-3150` (chave
pura, por decisão do Lucas, não `CLS-1283-CLS-3150`), a partir do master. Smoke = `lint:container` +
`GET /api/wallet/transactions` com e sem a env. Os docs antigos em `sdd/_specs|_plans` ficam.
Próximo: `/sdd-implement CLS-3150`; depois planejar CLS-3904/3905/3906.

**Plano do CLS-3906 (cms-v2) escrito no Jira em 2026-10-20**, label `sdd-plan`. O `mysql2` da raiz
fica (é o client de banco do Strapi). `_specs`/`_plans/CLS-2400.md` ficam. Verificar sempre com
`build:force`, porque um `dist` velho ainda registra o plugin. Smoke = `GET /_health` + uma rota com
bonus-list-picker, com e sem a env. Coleção de smoke ainda não existe em `tickets/CLS-1283/`.
**Implementado em 2026-10-21:** commit `bcae650` na branch `CLS-3906` (sem push), label `sdd-implement`.
Suíte 951/951, boot ok com e sem a env. O build do admin dá OOM local (exit 137, ~5,3 GB das outras
stacks); por decisão do Lucas, quem cobre o `build:force` é o build da imagem no CI, sem derrubar as stacks.

**2026-10-21:** coleção de smoke pronta em `tickets/CLS-1283/flipper-smoke/` (com `matrix.md` e `run.sh`),
linha de base 6/6 verde. Achados nos planos: 3905 cita `GET /api/ping` sem token, mas a rota é `/ping` e
exige token; 3906 pede uma página com campo bonus-list-picker, mas nenhum content type usa o campo.
BO `/wallet/transactions` dá 500 local por `BIGQUERY_KEY` inválido (ambiente, não o ticket).

**2026-10-21: CLS-3904 (BO) implementado**, branch `CLS-3904` a partir do master, não commitado; 7 arquivos, só deleções;
`make test` 3165 verde, sdd-reviewer limpo em 2 rodadas. `make lint` do BO só olha PHP adicionado/modificado, então é vazio aqui.
Falta a rota HTTP autenticada com e sem a env (smoke).

**2026-10-21, gateway (CLS-3905):** plano escrito via `sdd-plan`, implementado, commit `ceaa01c40` na
branch `CLS-3905`, **não pushado**; suite 2145 verde, reviewer sem achados, labels `sdd-plan` +
`sdd-implement`. Smoke local: token e `/ping` 200 com e sem a env; `/wallet/balances` 502 por causa da
wallet (vendor sem `BonusRollbackJob`, consertado na sessão da wallet), não do gateway.

**2026-10-21, wallet (CLS-3150):** commit `6ce833e74` na branch `CLS-3150`, **não pushado**; suite 1692
verde, `lint:container` ok, smoke `GET /api/wallet/transactions` 200 com e sem a env, reviewer sem achados
na 1ª rodada. Para rodar o master local foi preciso `make build` (imagem `latest-dev` puxada tinha PHP 8.4,
master exige 8.5.11) e renovar o token do `~/.composer/auth.json`. As branches `CLS-1283-*` vão precisar
de `make init` de novo.

**2026-10-21 ~11:10:** os 4 implementados e commitados, sem push: wallet `6ce833e74`, BO `e282e51b09`,
gateway `ceaa01c40`, cms-v2 `bcae650`. Revisados: só remoções, grep zerado, sem atribuição. Coleção 7/7
com e sem a env. Token do GitHub em `~/.composer/auth.json` estava expirado; renovado com `gh auth token`
(backup `auth.json.bak-2026-10-21`). Falta: push + PRs, DI (passo 14), pergunta de preprod (15).
**2026-10-21 ~11:15: PRs abertos** wallet #1917, backoffice #3267, gateway #1534, cms-v2 #141 (template do
time, sem vazamento). DI nos campos do Jira das 4 sub-tasks (sem ordem; env no argocd só sai depois, sem
rollback previsto) e completo em `tickets/CLS-1283/flipper-smoke/deployment-instructions.md`. CI verde
na wallet e no BO; gateway e cms-v2 sem CI (o dev não dispara no próprio PR). Falta: mover os tickets no
board (Lucas), passo 15 (preprod).

**Why:** o objetivo é não deixar rastro do Flipper nos nossos MS; o que os outros times usam não muda.
**How to apply:** próximo passo é `ticket-matrix`. Remoção pura, sem flag lida, então a matriz deve sair quase toda célula A.

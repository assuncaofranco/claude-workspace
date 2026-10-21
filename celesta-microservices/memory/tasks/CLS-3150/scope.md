---
name: cls3150-scope
description: "CLS-1283-CLS-3150 (remove remaining flags/migration code) — escopo fechado 2026-10-20: remover o Flipper inteiro de wallet, backoffice e gateway; promotion e game já limpos"
metadata:
  node_type: memory
  type: project
  originSessionId: 7c16fbf2-1a26-475a-8ca1-a2bb9c56e895
  modified: 2026-10-20T15:13:01.537Z
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

**Why:** o objetivo é não deixar rastro do Flipper nos nossos MS; o que os outros times usam não muda.
**How to apply:** próximo passo é `ticket-matrix`. Remoção pura, sem flag lida, então a matriz deve sair quase toda célula A.

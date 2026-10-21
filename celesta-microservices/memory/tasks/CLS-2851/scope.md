---
name: cls2851-scope
description: "CLS-2851 (game #1417, remoção da flag move_bonus_to_promotion) — único consumidor é o webhook Relax notifyFreespinsCancel; em pp1/pp2/pp4/prod-2 o game NUNCA leu a flag (sem FLIPPER_DATABASE_URL, default false) então o PR muda o destino do cancel de wallet para promotion nesses ambientes"
metadata:
  node_type: memory
  type: project
  originSessionId: 06eec600-3cc8-4bb3-aaab-ab74f8e17ae4
  modified: 2026-10-02T13:56:43.182Z
---

Papel: **testador**. PR celesta-game #1417, um commit `c0b78d713`, master sem drift em 2026-10-02.
Épico CLS-2847 (irmão: [[cls2847-cls2848-matrix]]).

**Único consumidor da flag no game:** `RelaxBundle/Handler/NotifyFreeSpinsCancelHandler` (webhook Relax
`notifyFreespinsCancel`, `promocode` = bonusId). Antes: flag ON → `PromotionClient::patchRewardBonus`,
OFF → `WalletClient::patchBonus`. Agora sempre promotion.

**Achado principal (2026-10-02):** o `FlipperClient` do game tinha `$defaultValue: false` e
`flipper_database_url` com `default::` vazio. Em `celesta-argocd-parameters` só **prod-1, staging-1 e
preprod-3** têm `FLIPPER_DATABASE_URL` na sealed secret do game (commits de jul e set/2026). Em **prod-2,
preprod-1, preprod-2, preprod-4** o game sempre foi pelo **wallet**, mesmo com a flag ON no promotion.
Lá o PR não é só limpeza, ele muda o comportamento. Provavelmente conserta uma divergência: o wallet
cancelava o sub_balance e o bônus do promotion ficava vivo (padrão do healthcheck 089). `PROMOTION_HOST`
existe em todo ambiente.

**Cadeia real depois do PR:** Relax → game → promotion `PATCH reward/bonus/{id}` → `BonusService::cancel`
(flush → `BonusListener` chama `gameClient->cancelFreeRound` por gameId, erro só logado) → wallet
`refundBonusTransaction` (erro só logado, devolve null). O teste de controller do game mocka o promotion,
então essa cadeia nunca foi exercitada em teste.

Local: game em CLS-2851, lint:container ok, 6/6 testes direcionados ok. Game já deployado em PP1
(Lucas, 2026-10-02).

**Newman local verde em 2026-10-02** (16 req / 30 asserções), coleção em `~/.claude/postman/CLS-2851/`.
Os três bancos batem depois do cancel (bonus, sub_balance por `bonus_id` e free_round_grant, todos
`canceled`). Truque local: o Relax não existe, então o launch vem antes do claim (o grant fica `pending`).

**Achado anterior ao PR:** `RelaxProvider::mapWalletToRelaxError` tem `default => DAILY_TIME_LIMIT`, então
qualquer 4xx do promotion (repetição de cancel, bônus inexistente) chega ao Relax como limite diário e o
grant **não** é marcado como cancelado.

**PP1, 2026-10-02:** código da branch confirmado no pod. Nenhum grant Relax `pending/started` antigo,
ou seja, nenhum órfão. Newman verde (`run-pp1.sh`: domínio 56, player 282570 = `sub` do token do
lucastest, jogo **55672** Money Train 3 com gateway 41 e studio 562; o 55388 está com metadata inativo e
o launch dá 404). Bônus 1165837 com promotion, wallet e grant todos `canceled`. Sobra minha da primeira
rodada: bônus 1165835 `claimed`, com grant 3496 `pending` no jogo inativo, e o 1165836 `offered`. O cron
de expiração vai pegar os dois.

**Falta:** a mesma checagem de órfãos em **prod-2**, que é produção, então quem roda é o Lucas.

---
name: cls1546-max-bet-activity
description: CLS-1546 (3318 game + 3319 BO) — activity max_bet_limit_updated centralizado no game com origem obrigatória; decisões e lembretes de entrega
metadata:
  node_type: memory
  type: project
  originSessionId: 9ae3c54a-e4cf-43f8-a2ed-299e2136b861
  modified: 2026-10-06T14:58:36.116Z
---

**Problema:** a action "Update maximum bet amount" do cenário altera o max bet direto no game, e só o BO despachava `max_bet_limit_updated`, então nada aparecia na aba Logs do cenário.

**Decisões (2026-10-06):**
- O game despacha o activity no PUT e no PATCH, um job por categoria alterada, com o payload igual ao que o BO mandava (`before_value`, `after_value`, `internal_game_category_name`, ...). O `company_id` sai: ninguém consome.
- Origem: `scenario` + scenarioId, ou `backoffice` → `user` + id do agente. **`_source`/`_sourceId` obrigatórios** no PUT/PATCH (400 sem eles). Isso diverge da wallet, que cai em `user`; registrar na spec.
- BO (3319): para de despachar, faz `propagateSource($userId)` nos dois métodos e perde GET antes, categorias e `getCustomerById`.
- Não renomear `sourceUserId` (contrato da job-library inteira).
- DELETE e `maximum-bet-defaults` ficam fora.
- Entregas: game, BO e **PR no proteus** ([[project-proteus-pr-procedure]]). **Front não entra.**

**Estado 2026-10-06 (fim do dia):** tudo pushado, PRs abertos e prontos:
- celesta-game #1421, `CLS-1546-CLS-3318`: suíte completa verde (1268);
- celesta-backoffice #3226, `CLS-1546-CLS-3319`: suíte completa verde localmente (3036 testes, terminou depois do push);
- celesta-qaa-proteus #618, `CLS-1546-CLS-3318`.

E2E local pelo BO confirmado: o PUT chega no game com `_source=backoffice`, delta de 2 mensagens em `dev-activity`, o PATCH sem mudança dá 0 e o PATCH com mudança dá 1. Caminho do cenário coberto só pelos testes do game. Se o CI falhar, Lucas pede para olhar no dia seguinte.

Gotchas de ambiente desse dia: a master do BO exige PHP 8.5 (`make build`); o `make init` morria com 137 porque o container reiniciava em loop no meio do `composer install` (resolvido com `docker compose run --rm --no-deps --entrypoint sh php -c "composer install"` antes do init); o nome de `game_internal_category` no banco de teste depende da ordem dos testes.

**Lembretes para o Lucas:**
- Pedir ao **PO** que teste a aba Logs do cenário. O formatter de lá (`formatScenarioLogs.js:72`, CEL-3080) espera uma lista de categorias num log só e a string `"null"`, um formato que nunca existiu; vai renderizar errado.
- Pedir ao **time de front** que alinhe esse formatter ao formato do log do player.
- Pedir ao **time C** que o handler do cenário faça GET + merge antes do PUT: hoje ele manda uma categoria só e o PUT (replace) apaga as outras. O log vai passar a mostrar isso (`Live: 50 → Unlimited`).
- 3318 e 3319 sobem juntos; o BO não pode ir depois do game.

**Estado 2026-10-07:** review independente feito e reparos aplicados (testes de todas as células A, spec corrigida sobre `company_id` e DELETEs). Instruções de deploy em `claude-workspace/celesta-microservices/tickets/CLS-1546/deployment-instructions.md` e na descrição dos três PRs. O CI do `proteus / isolated-tests` está quebrado por motivos externos: o token npm do QAA-1107 falta no template `celesta-ci-templates` e o mock de promotion do CLS-2847 ainda não foi mergeado (celesta-qaa-mock #230). O branch do proteus voltou para `b0a6bc17` (antes do merge da master), o que destravou o game. O BO espera as duas correções do QAA. **Decisão do Lucas:** o front fica fora; a aba Logs do cenário quebra depois do deploy do game, e ele mostra o erro ao PO.

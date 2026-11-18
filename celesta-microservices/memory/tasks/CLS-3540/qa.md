---
name: cls3540-qa
description: "QA do refactor de cobertura do cms (#281, Rasoul) — coleção pronta e verde no pp1 antes do deploy; falta rodar completa depois do deploy da branch"
metadata:
  node_type: memory
  type: project
  originSessionId: c3586f16-e41f-4c98-912b-e1a78321d26c
  modified: 2026-11-03T12:10:08.975Z
---

Lucas como testador. Matriz em `claude-workspace/celesta-microservices/tickets/CLS-3540/matrix.md`, coleção e
runbook em `postman/CLS-3540/` (`./run-pp1.sh`).

**2026-11-03:** pp1 antes do deploy (folders 0-3 e 5): 35 requests, 93 assertions, 0 falhas. Domínio 56 tem
`en,fr`; o `lucastest` (282570) está nos segmentos 2189, 2193, 2202, 2228, 2252. Testes de controller do PR
verdes no local (86).

**2026-11-03, depois do deploy** (imagem `CLS-3540-2780730`, código da branch conferido no pod): todas as células
A verdes; rascunho de T&C 11 (fica na lista, sem rota de delete), activity com o mesmo formato de antes. Único
vermelho: BO `GET terms_and_conditions` 403 para o usuário do vault (permissão do BO, não do cms; no CLS-505 o Lucas
tinha concedido, sumiu). Activity de T&C se lê pelo BO `POST /api/gateway/logs` (sem domínio na rota).

Armadilhas pagas:
- GW `/cms/content-blocks` responde com a chave `content-block`, não `contentBlock`.
- BO `POST /api/gateway/player/segments` (sem domínio na rota) quer `{"filter":{"playerIds":[..]},"limit","offset"}`;
  `playerIds` na raiz dá 400 "extra fields".
- O 400 de body com tipo errado não chega pelo gateway: o form dele valida tipo antes.

---
name: cls505-qa
description: "QA do upgrade Symfony 7.4 (CLS-505): game/contact/cms verdes no local em 2026-10-13, coleções prontas para pp1; promotion bloqueado pelo Proteus; armadilhas do ambiente local"
metadata:
  node_type: memory
  type: project
  originSessionId: 021a75bb-af4b-402b-b068-e4110dfaefc3
  modified: 2026-10-13T10:58:58.716Z
---

Lucas como testador. PRs: game #1426 (CLS-505-CLS-3288), contact #424 (CLS-3290), cms #276 (CLS-3291),
promotion #548 (CLS-505-CLS-3289).

**Estado 2026-10-13:** as três coleções em `claude-workspace/celesta-microservices/postman/CLS-505/`
rodaram verdes no local (game 25/38, contact 5/6, cms 32/40). pp1 espera o promotion, **não** porque
precisa testar junto, mas porque o PP1 estava em uso. Promotion: Proteus vermelho só nessa branch
(pcpr-11 reward configs com `segmentIds` undefined, pcpr-13, pcpr-9, pcpr-1); outras branches passam.

Decisões e achados:
- Testar separado não obriga refazer: só promotion + fluxos cruzados game↔promotion (free rounds,
  pasta 4 do game). Exceção: se a correção do promotion cair numa lib `CLS-505`, retestar os outros.
- **Nunca publicar termos e condições em pp1**: trava todo player do domínio até assinar.
- cms `send`/`render`/`render/bulk` não têm rota no BO (bulk é do scenario); só DEV-ONLY.
- Evolution só confere `authToken` depois de achar sessão, e o token não é legível em pp1 → Datadog.
- Rollback Relax grava `related_transaction_id` (conferido no banco local).

Armadilhas do local (custaram a sessão):
- `localsqs`/`elasticsearch` vêm do `celesta-global-container`; sem eles o `make init` de game/cms
  falha nas fixtures e o segment devolve null → gateway 502 em `/reward/bonuses`.
- `make init` dos cinco em paralelo estoura os 8 GB do Docker (exit 137).
- gateway master exige PHP 8.5: `make build`, depois `composer install` num `run --rm`, porque o
  roadrunner cai no boot com vendor velho e o `exec` do install morre junto (também 137).
- Player 1 das fixtures começa com saldo negativo; pasta 1b da coleção recarrega pelo BO
  (`adjustment_up`, motivo `technical_issue`; `refund` não vale para up).

**PP2, 2026-10-13:** promotion 42/51, contact 5/6, cms 28/35, todos verdes. Game no PP2 só leitura
do BO + launch: o domínio 56 lá só tem jogos CGA (Quanta), cujos webhooks exigem credencial do gateway
que não é legível; bet/win/rollback fica no PP1 (Relax). Player de teste do PP2: id 307847 (vault).
Permissões concedidas ao role `head_of_operations` (3906, **51 usuários**) no `pp2_backoffice`:
policy 37 `ROLE_BONUSES`. No PP1 o Lucas concedeu email provider e T&C list. As tabelas ficam em
`pp1_backoffice`/`pp2_backoffice` no mesmo RDS de preprod.

**PP1, 2026-10-14, fechado:** game pastas 1, 2 e 4 verdes com o `lucastest` (recarregado com 100 EUR);
rollback com `related_transaction_id` conferido no `pp1_game` (10765352 → 10765351, bet). Os 4 tickets
foram para Implemented. Só resta observar no Datadog depois do deploy de prod.

Ver [[cls3290-review]].

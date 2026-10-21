---
name: cls850-review
description: "CLS-1283-CLS-850 review (Bohdan) — wallet #1912 (release 1, code) + #1913 (release 2, rename migration) + proteus #668; findings drafted 2026-10-19, not posted"
metadata:
  node_type: memory
  type: project
  originSessionId: 7ba8e73a-ca0a-4cad-9fb3-5710eada7934
  modified: 2026-10-19T14:59:37.167Z
---

Ticket do Bohdan, subtask do CLS-1283. Jira sem descrição; spec/plano em `sdd/_specs|_plans/CLS-1283-CLS-850.md` (SDD antigo). Escopo cresceu de "renomear 5 colunas" para também tirar `bonus_model`, `bonus_model_segment`, `free_round_configuration`, `bonus_to_claim` (entidades, rotas, release 2 renomeia para `old_*`). job-library #502 (meu, jun/2026, branch CLS-392-CLS-850-1) **não** é deste ticket.

Achados confirmados 2026-10-19:
- Descartados pelo Lucas: composer em dev-branch (troca para tag só no fim, padrão do time) e pedidos de proteção hipotética (lock timeout, COPY no down). Conflitos com outros PRs também fora: review se restringe ao código do ticket.
- #1912 migrated bonus (bonus_model_id set) agora pega o cap via `getBonusData(bonus_id ?? id)`; linha sem bonus na promotion (CEL-6848 pulou) → 404 → TTR pulado para sempre. Pedir a query de contagem antes do release 1.
- #1913 migration sem `lock_wait_timeout` (spec exige); `down()` readiciona FK com `ALGORITHM=COPY` (rebuild de ~22M linhas, falha com órfão).
- proteus `CLS-1283-CLS-850-migration` = mesmo commit do release 1; qaa-mock sem branch.
- Conflita com o nosso #1911 (CLS-2485) em 9 arquivos (`CancelBonusCommand` apagado lá, alterado aqui) e com a pilha CLS-1624 (#1909) em 34.
- Spec com texto velho (AC diz que offer/claim-multiple continuam; foram apagados).

Related: [[cls2485-scope]]

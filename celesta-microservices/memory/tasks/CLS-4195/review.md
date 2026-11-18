---
name: cls-4195-review
description: "Review do gateway #1545 (Bohdan, pai CLS-3701): checagem de moeda bônus × depósito no POST /payment; código ok, só o local do plano diverge do playbook"
metadata:
  node_type: memory
  type: project
  originSessionId: 0355ff5d-7126-4cdf-922c-a66b31b5f62f
  modified: 2026-11-02T15:51:10.621Z
---

Gateway PR #1545, branch `CLS-3701-CLS-4195`, autor Bohdan. Revisado em 2026-11-02.

- Código bate com a spec do CLS-3701 e com o plano. `rewardConfiguration.currency` do `bonus_list` da promotion é sempre preenchido (BonusNormalizer), então ler a moeda em todo bônus da lista não estoura.
- O plano está em `_plans/` (pasta do SDD antigo, que o repo usa como precedente). O playbook 0.44.0 diz `.sdd/_plans/<KEY>.md` "whatever the repository's other conventions", e o `sdd-implement` 0.44 recusa sem esse arquivo. Único comentário a postar, não bloqueante.
- Mover os mocks de bônus da promotion de `MockCurlClientRequestsTrait` para `PromotionClientMockTrait` tem lógica: a promotion já tinha o trait dela, com `PROMOTION_HOST`; os 7 blocos JSON repetidos viraram um builder; os dados ficaram equivalentes e nenhum consumidor quebra (`GatewayTestCase` ainda usa o trait curl, `BonusControllerTest` já usava o da promotion). Não comentar.
- O phpunit não tinha rodado no CI quando revisei. No local deu erro de fixture do alice, por causa do vendor da CLS-3905; não é o PR.

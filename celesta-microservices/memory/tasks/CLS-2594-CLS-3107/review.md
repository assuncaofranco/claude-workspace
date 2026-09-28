---
name: cls2594-cls3107-review
description: "Review do CLS-3107 (endpoints de gift no celesta-backoffice + fixtures) iniciado em 2026-09-24: divergências pai × implementado e o assert de policies quebrado"
metadata: 
  node_type: memory
  type: project
  originSessionId: a965f863-52b9-4c37-9b13-32fabfc529bd
  modified: 2026-09-24T09:31:51.371Z
---

# CLS-2594 / CLS-3107 — gateway de gift no backoffice

Dois PRs: celesta-backoffice #3194 e celesta-fixtures #290, os dois `CLS-2594-CLS-3107 → master`.
Em 2026-09-24 as duas branches **já continham master inteiro** — nada a mergear.

O CLS-3107 é só a camada de gateway: `GiftController` com `POST .../gift` e `GET .../gifts`,
proxy para o promotion (CLS-3055), mais duas policies novas. Nenhuma entidade Doctrine.
O que é um gift e onde mora o KPI está em [[cls2594-cls3055-gift-review]].

## Renomeação value ↔ amount

O front escolheu `value`, o promotion `amount`. A tradução acontece em quatro lugares: request,
resposta, mapa de erros (`mapPromotionErrors`) e mapa de ordenação (`PromotionClient::GIFT_API_FIELDS`).
É o eixo onde um bug desses endpoints tende a aparecer.

## Divergências pai × implementado (2026-09-24)

O spec cobre com uma linha só — *"the reduced field set agreed with the team lead"* — sem razão nem
consequência. Justificadas de fato: currency delegada ao promotion, quantity removida, árvore de
permissões (bate com o print do pai). **Não** justificadas:

- **`Date gifted` removida.** O pai diz que esse campo *drives KPI attribution (CLS-2957)*. Sem ele,
  `created_at` vira a data do KPI — presente entregue em dezembro e digitado em janeiro cai em janeiro.
- **Sem cancel / status `canceled`.** O pai define cancelar como o **único** caminho de correção
  ("gift records are not editable"). Sem ele não sobra caminho nenhum.
- **`Reason` removida** (Birthday/Christmas/Easter/Valentine's/Other). Hoje não alimenta nada.
- **Activity log.** Open Question 1 do spec, assumida como "fora", nunca respondida. O bônus manual
  dispara `EVENT_MANUAL_BONUS_OFFERED`; o gift não dispara nada porque o evento não existe na
  job-library.

## Achado de contagem de policies — confirmado e já corrigido pelo autor

`PolicyControllerTest::testGetPolicies` afirmava `assertCount(98, ...)` enquanto o `composer.lock` já
apontava para as fixtures da branch (+3 policies). O autor (Socrates) corrigiu sozinho no commit
`e731b266` "fixed policy tests": **quatro** testes fixavam a contagem, não um —
`PolicyControllerTest`, `UserControllerTest` e `ProfileControllerTest` (duas vezes) — todos de 98
para 101. Detalhe durável em [[celesta-backoffice-permission-tree]].

**Lição de processo:** eu tentei derivar o número somando as entradas do YAML das fixtures (90 → 93) e
não fechava com 98, porque parte das policies do banco de teste vem de migration, não de fixture.
Contagem absoluta em teste não se confere por aritmética de YAML — ou se roda, ou se pergunta.

## Comentários postados (2026-09-24)

Review `COMMENTED` no PR #3194, 7 comentários inline, todos no head `e731b266`:

1. `_specs:27` — `Date gifted` removida sem a consequência registrada (`created_at` vira a data do KPI)
2. `_specs:28` — sem cancel, e cancelar é o único caminho de correção que o pai define
3. `_specs:126` — Open Question 1 (activity log) foi para o merge ainda aberta
4. `_specs:147` — o spec afirma cobertura que não existe: o mapeamento `value`→`amount` mora no form
   (`SortQueryType` + `GIFT_API_FIELDS`), não no normalizer, e nada manda `order[field]=value`
5. `GiftController.php:64` — copiou a checagem marcada com `TODO: Remove` no `RewardController`
6. `GiftNormalizer.php:32` — `description` vazia chega como `''`, o `?? null` não pega (mesmo
   comentário que eu já tinha feito no PR 531 do promotion)
7. `OfferType.php:19` — schema diz `maxLength: 3`, a constraint virou `Regex('/^[A-Za-z]{3}$/')`

Retirado antes de postar: `filter[ownerIds]` sem asserção no teste de controller — o `mockMethod` só
guarda o path e nenhum mock do repositório assere query string, então não é omissão do autor.

## O que eu errei

Levantei que a policy pai `PLAYER_ACTIONS` talvez não existisse, a partir das fixtures. Existe desde
CEL-2437 (2025-06) — e o **plano já dizia**, em duas linhas. Ler spec e plano inteiros antes de
levantar ponto de migration. Sem DI de insert manual.

A DI que **é** real: ordem de deploy — promotion CLS-3055 e release de constants antes, front CLS-3074
depois.

## Pendências de deploy

`composer.json` com dois pins de branch: `lancasters/constants: dev-CLS-2594-CLS-3054 as 1.336` e
`lancasters/celesta-fixtures: dev-CLS-2594-CLS-3107`. Lucas confirmou em 2026-09-24 que está ok assim
por enquanto.

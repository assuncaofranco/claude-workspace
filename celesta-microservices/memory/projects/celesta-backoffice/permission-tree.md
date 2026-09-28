---
name: celesta-backoffice-permission-tree
description: "Árvore de policies/permissions do celesta-backoffice: PLAYER_ACTIONS existe desde CEL-2437 (2025-06), e as fixtures do vendor estão paradas no layout anterior"
metadata: 
  node_type: memory
  type: project
  originSessionId: a965f863-52b9-4c37-9b13-32fabfc529bd
  modified: 2026-09-24T09:08:26.205Z
---

# Árvore de permissões do celesta-backoffice

`policy` e `permission` são coisas diferentes. A **policy** é o nó da árvore que a tela desenha e o
front lê pelo nome; a **permission** é o que o backend checa no token. Uma policy carrega uma
permission de nome diferente — `ROLE_PLAYERS_BONUS_TAB` → `PS_BONUS_LIST`,
`ROLE_PLAYERS_ACTIONS_GIVE_BONUS` → `PS_BONUS_OFFER`. Nenhuma carrega permission com o próprio nome.

## PLAYER_ACTIONS existe — as fixtures é que não sabem

`src/Migrations/Version20250604000000.php` (CEL-2437, junho/2025) cria a policy `PLAYER_ACTIONS`
com pai `ROLE_PLAYERS` e rependura nove policies de ação debaixo dela
(`ROLE_PLAYERS_ACTIONS_GIVE_BONUS`, `..._MAKE_ADJUSTMENT`, `..._LOCK_ACCOUNT`, etc.).

As fixtures do `lancasters/celesta-fixtures` **não** refletem isso: em `src/backoffice/07_policies.yml`
as policies de ação continuam com pai `ROLE_PLAYERS_PAGE_ACCESS` (o layout pré-CEL-2437), e
`PLAYER_ACTIONS` simplesmente não existe até a branch do CLS-2594-CLS-3107 adicioná-la.

**Consequência prática:** ao revisar uma migration que cria policy com `INSERT ... SELECT` a partir do
pai pelo nome, não concluir "o pai não existe" a partir das fixtures. Fixtures divergem do banco real.
Procurar a migration que criou o pai antes de levantar o ponto — foi o erro que eu cometi em
2026-09-24 no review do [[cls2594-cls3107-review]].

O `INSERT ... SELECT` falha **em silêncio** quando o pai não existe: zero linhas, migration verde,
policy nunca criada. É um risco real do padrão, só não é o caso quando o pai vem de migration antiga.

## Contagem de policies nos testes

`tests/GatewayBundle/Controller/User/PolicyControllerTest::testGetPolicies` afirma um número absoluto
(`assertCount(98, ...)` na v1.222 das fixtures). Toda branch que adiciona policy às fixtures **e**
aponta o composer para a branch de fixtures tem que subir esse número junto, senão o CI fica vermelho
por aritmética, não por bug.

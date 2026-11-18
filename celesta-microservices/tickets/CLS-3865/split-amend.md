# CLS-3865 — emenda do split (fase 0)

`sdd-split` 0.61.0 (versão igual à do `main`), rodado em 2026-11-18 até o passo "ask whether to create".
**Nada foi escrito no Jira.** Fontes: spec atual do pai (Backlog, `updated` 2026-11-18 06:31 UTC), as 10
sub-tasks, a tabela Team components do Notion, `decisions.md`, `matrix.md` e o código em `origin/*`
(fetch de hoje).

> **CLS-3865** — Edit gift value and complete gifts to order · Story · components A, B, D, F · status
> Backlog · 5 SP · 10 sub-tasks existentes · labels `sdd-split`

O título do pai ainda diz "gifts to order"; não é do split mexer nele (só components e label).

## Readiness

1. What exists today: respondido (Problem statement: `claimed` final, KPIs contam claimed, §3.2).
2. Done when: respondido (19 ACs).
3. Decided / out: respondido (Scope OUT, incluindo "column choice is front-end only").
4. Surfaces: respondido indiretamente (promotion, statistics, BO, front, activity, BI, constants, job-library).

## Resultado

- **Nenhuma sub-task nova, nenhuma recriada, nenhuma apagada.**
- Mudam: **4940, 4942, 4943, 4944** (título e/ou todo list). As outras seis ficam como estão.
- Links `Blocks`: nenhum novo, nenhum removido. Conferido: a lista de domínio aceita `statuses` como string
  livre (`Gift/FilterType.php:43`, sem choices de constante), então a 4940 filtrar `completed` não depende
  da 4935. O DAG continua acíclico.
- Story points: as amendadas mantêm os pontos (regra do skill). Nota: a 4944 tem 5 SP e a página já existe
  na branch `CLS-3865` do front (PR #2307); talvez caia, mas é do Dimitris.
- Diferente do esperado: a **4943 não fala de "Gifts to order" nem de abas** (é a aba Gifts do player). A
  mudança nela é outra: texto de ajuda do Edit value e, se aprovado, labels de permissão (pergunta 1).

## 1. Mapa de cobertura (requisito do pai → sub-task)

| Requisito da spec | Sub-task |
|---|---|
| Status `completed`, só a partir de `claimed` | 4935 (constante), 4941 (transição) |
| Edit value em claimed, moeda inalterada, > 0 e 2 casas | 4941 (API), 4942 (proxy), 4943 (aba do player), 4944 (To order) |
| Página Gift checkout, entrada no menu, abas To order (claimed) e Ordered (completed, read-only) | 4944; proxy 4942 |
| Lista de domínio por status (`claimed`, `completed`) e moeda, mais antigo primeiro, paginada | **4940** (muda); proxy **4942** (muda) |
| Colunas: status, gift ID, name, value, currency, player ID, offered by/at, approved by/at | 4944 (escolha de coluna no front); 4940 só devolve campos que já existem (Scope OUT) |
| Painel lateral ao clicar na linha, nome sem link | 4944 |
| Approved by/at com "—" fora de request aprovado | 4940 (dado), 4944 (render) |
| Empty state por aba | 4944 |
| Completed passa de To order para Ordered; canceled sai do Gift checkout; ambos ficam na aba do player | 4940 (filtro), 4944, 4943 |
| Edit value clicando no valor em To order; texto de ajuda "Counted in generosity when the gift is completed." | 4944; 4943 (mesmo modal na aba do player) |
| Complete com confirmação | 4943, 4944 |
| Cancel em To order só com _Cancel gift_ (CLS-3508) | 4944 |
| Completed sem ação, valor não clicável; API rejeita edição ou transição | 4941, 4943, 4944 |
| Config disabled/deleted ainda editável, concluível, cancelável | 4941 |
| Duas ações simultâneas | 4941 (texto "first change wins" mantido; ajuste com o PO, decisão 7) |
| Status change para statistics; edição sozinha não manda nada | 4941 |
| KPIs só com completed, valor e período de conclusão | 4938 (statistics), 4939 (BI, Implemented) |
| Gift anterior ao release | sem regra (decisão 1); AC a propor ao Francisco. 4938 já diz isso |
| Só _View gifts_: vê tudo sem ação, 403 em mudança | 4942 (403), 4943, 4944 (sem ação, valor não clicável) |
| Grants: Give gift → Edit gifts, Access Gift tab → View gifts | 4942 (chaves técnicas mantidas, relabel) |
| Eventos `gift_value_edited` e `gift_completed`, um por sucesso | 4936, 4937 (Implemented), 4942, 4943 (render nos Logs) |
| Labels em 6 locales (status, ações, página, aba, permissão) | 4942, 4943, 4944; **permissão no front: lacuna, pergunta 1** |
| Atualizar compêndio §3.2 | **sem sub-task**: é Notion, não repositório. Pergunta 2 |

Sub-task → requisito: todas as dez rastreiam a um requisito acima. Nenhuma existe só por cleanup ou
compatibilidade.

Compatibilidade: a lista de domínio já existe e só ganha uso; o relabel mantém as chaves técnicas; a
statistics sobe antes do Complete da promotion (4938 bloqueia 4941, já linkado). Nada novo nesta emenda.

## 2. Sub-tasks que mudam

### CLS-4940 — promotion (D-Team, 3 SP)

**Antes**

`{D} [promotion] Domain list of claimed gifts with requester and approver`

```
* starts from branch CLS-4540 (gift requests)
* list the domain's `claimed` gifts across players, oldest first, filterable by currency
* return gift ID, player ID, name, reason, value, currency, created by and created at
* return requested by, approved by and approved at when the gift comes from an approved request, empty otherwise
* document it in the OpenAPI schema; cover with tests

Done when one call returns every claimed gift of a domain with its request information.
```

**Depois**

`{D} [promotion] Domain gift list by status (claimed, completed) with offer and approval data`

```
* list the domain's gifts across players, filtered by status (`claimed`, `completed`) and currency, oldest first
* paginate with the limit and offset the list already accepts
* return the existing gift fields the Gift checkout needs: status, gift ID, name, value, currency, player ID, offered by, offered at, approved by, approved at
* offered by is the backoffice user, the scenario or the promotion that gave the gift
* for promotion gifts, read the gift source added by CLS-4770; do not add another one here
* approved by and approved at only for gifts from an approved request, empty otherwise
* a canceled gift is in neither status result
* document it in the OpenAPI schema; cover with tests

Done when one call per status returns every claimed or completed gift of a domain, page by page, with who offered and who approved it.
```

Motivo: spec de 17/11 (filtro por status, paginação, colunas novas; Scope OUT diz que o endpoint devolve
os campos que já existem). A linha "starts from branch CLS-4540" sai porque a CLS-4540 está no master
(#591). "Reason", "created by/at" e "requested by" saem das colunas. Scenario: decisão 4. Promoção: matriz
#23, dependência da CLS-4770 (outra story, CLS-3916), por isso sem link `Blocks` (o skill só liga irmãs).

### CLS-4942 — backoffice (B-Team, 5 SP, Maksat)

**Antes**

`{B} [backoffice] Edit value, complete and gifts-to-order proxies, View/Edit gifts labels, activity events`

```
* starts from branches CLS-4437 (cancel) and CLS-3094-CLS-4542 (gift requests)
* bump celesta-job-library to the version with `gift_value_edited` and `gift_completed`
* proxy edit value and complete to Promotion, gated by `PS_GIFT_OFFER`, otherwise 403
* proxy the domain claimed-gifts list, gated by `PS_GIFT_LIST`, otherwise 403
* keep the technical keys; relabel the policies to "View gifts" and "Edit gifts" (decided in conversation, 2026-11-12)
* pass Promotion's rejections back as errors (invalid value, wrong status, simultaneous action)
* after a successful action, dispatch `gift_value_edited` (old value, new value, currency) or `gift_completed` (name, value, currency); a failed action dispatches nothing
* allow both events in the BO Logs filter and describe them in player Logs; event and permission labels in 6 locales
* cover the proxies, the permissions and the dispatches with tests

Done when the front can list, re-value and complete claimed gifts, a user with View gifts only gets 403 on any change, and each action writes one Logs entry.
```

**Depois**

`{B} [backoffice] Edit value, complete and Gift checkout proxies, View/Edit gifts labels, activity events`

```
* starts from branch CLS-4437 (cancel)
* bump celesta-job-library to the version with `gift_value_edited` and `gift_completed`
* proxy edit value and complete to Promotion, gated by `PS_GIFT_OFFER`, otherwise 403
* proxy the domain gift list for Gift checkout, with the status (`claimed`, `completed`), currency and pagination filters, gated by `PS_GIFT_LIST`, otherwise 403
* these routes are the contract the Gift checkout page uses; the page follows them
* keep the technical keys; relabel the policies to "View gifts" and "Edit gifts" (decided in conversation, 2026-11-12)
* pass Promotion's rejections back as errors (invalid value, wrong status, simultaneous action)
* after a successful action, dispatch `gift_value_edited` (old value, new value, currency) or `gift_completed` (name, value, currency); a failed action dispatches nothing
* allow both events in the BO Logs filter and describe them in player Logs; event and permission labels in 6 locales
* cover the proxies, the permissions and the dispatches with tests

Done when the front can list claimed and completed gifts, re-value and complete claimed ones, a user with View gifts only gets 403 on any change, and each action writes one Logs entry.
```

Motivo: lista por status e paginada; nome da página; decisão 8 (o contrato segue as rotas da 4942, não as
que a página chama hoje). CLS-3094-CLS-4542 está no master do backoffice (#3319), por isso sai da linha de
base.

### CLS-4943 — backoffice-front (F-Team, 3 SP, Dimitris)

**Antes**

`{F} [backoffice-front] Edit value and Complete in the player Gifts tab, new events in player Logs`

```
* starts from branches CLS-4438 (cancel action) and CLS-4545 (Gifts tab blocks)
* show Edit value and Complete on claimed gifts for users with Edit gifts
* Edit value: value greater than 0, at most 2 decimals, currency read-only; an invalid value is rejected
* Complete asks for confirmation; dismissing changes nothing
* add the Completed status label; no action on a completed gift
* show the API error when an action is rejected
* render `gift_value_edited` and `gift_completed` in the player activity log
* say "completed gifts" where the Generosity KPI description says claimed gifts
* labels in 6 locales; cover with tests

Done when a user with Edit gifts can re-value and complete a claimed gift from the player page, and a user with View gifts only sees no action.
```

**Depois** (título igual)

`{F} [backoffice-front] Edit value and Complete in the player Gifts tab, new events in player Logs`

```
* starts from branches CLS-4438 (cancel action) and CLS-4545 (Gifts tab blocks)
* show Edit value and Complete on claimed gifts for users with Edit gifts
* Edit value: value greater than 0, at most 2 decimals, currency read-only, help text "Counted in generosity when the gift is completed."; an invalid value shows an inline error and nothing is saved
* Complete asks for confirmation with the gift, value and currency; dismissing changes nothing
* add the Completed status label; no action on a completed gift and its value is not clickable
* show the API error when an action is rejected
* render `gift_value_edited` and `gift_completed` in the player activity log
* say "completed gifts" where the Generosity KPI description says claimed gifts
* rename the permission labels to "View gifts" and "Edit gifts" where the front shows them   <- só se a pergunta 1 for "sim"
* labels in 6 locales; cover with tests

Done when a user with Edit gifts can re-value and complete a claimed gift from the player page, and a user with View gifts only sees no action.
```

Motivo: ACs de Edit value (texto de ajuda, erro inline), Complete (gift, valor, moeda) e completed sem
valor clicável. A linha de labels de permissão fecha a lacuna da matriz #65 (os labels que a tela mostra
moram no front, `en.js:153,177`; no BO só existe "Give gift").

### CLS-4944 — backoffice-front (F-Team, 5 SP, Dimitris)

**Antes**

`{F} [backoffice-front] Gifts to order page and Gifts menu entry`

```
* add the Gifts entry in the left menu and the Gifts to order page, visible with View gifts
* columns: gift ID, player ID (link to the player page), gift name, reason, value, currency, created by, created at, requested by, approved by, approved at, actions
* oldest first, filter by currency, empty state when there is no claimed gift
* show "—" for requested by, approved by and approved at when the gift has no request
* reuse Edit value and Complete; show Cancel only with Cancel gift, behaving as in the player tab
* a completed or canceled gift leaves the list
* labels in 6 locales; cover with tests

Done when a user can work through every claimed gift of the domain from one page.
```

**Depois**

`{F} [backoffice-front] Gift checkout page with To order and Ordered tabs, and its menu entry`

```
* starts from branch CLS-3865 (Gift checkout page, PR #2307)
* add the Gift checkout entry in the left menu and the page, visible with View gifts
* two tabs: To order (claimed gifts) and Ordered (completed gifts, read-only)
* columns in both tabs: status, gift ID, gift name, value, currency, player ID (link to the player page), offered by, offered at, approved by, approved at
* oldest first, filter by currency, paginated, empty state per tab
* show "—" for approved by and approved at when the gift does not come from an approved request
* clicking a row opens a side panel with the gift info; the gift name is plain text
* To order: Edit value by clicking the value, reusing the player tab rules and help text; Complete with confirmation; Cancel only with Cancel gift, as in the player tab
* Ordered and View-gifts-only users: no action, value not clickable
* a completed gift moves from To order to Ordered; a canceled gift leaves the page
* use the backoffice routes CLS-4942 defines for the list, edit value and complete
* remove the Adjustment action, the supplier order reference, the Delivery card and the "marked as ordered" wording
* page, tab, status and action labels in 6 locales; cover with tests

Done when a user can work through every claimed gift of the domain from To order and find every completed one in Ordered.
```

Motivo: spec de 17/11 (nome, abas, colunas, painel lateral, valor clicável, paginação). Decisões 8 e 8b
(Adjustment, order reference e delivery saem; contrato da 4942). A página já existe na branch `CLS-3865`
do front (`87dc6f3c9`, PR #2307, aberto), com abas "To order"/"Ordered" e painel lateral; ela chama
`POST …/gift/{id}/complete`, `PATCH …/gift/{id}`, `POST …/gift/{id}/adjustment` e `GET …/gifts/count`.

## Sub-tasks que não mudam

| Sub-task | Por quê |
|---|---|
| [CLS-4935](https://celesta.atlassian.net/browse/CLS-4935) constants | status e transição iguais |
| [CLS-4936](https://celesta.atlassian.net/browse/CLS-4936) job-library | eventos iguais (ver pergunta 3 sobre o component) |
| [CLS-4937](https://celesta.atlassian.net/browse/CLS-4937) activity | Implemented; eventos iguais |
| [CLS-4938](https://celesta.atlassian.net/browse/CLS-4938) statistics | regra de KPI igual |
| [CLS-4939](https://celesta.atlassian.net/browse/CLS-4939) terraform-bi | Implemented; regra igual |
| [CLS-4941](https://celesta.atlassian.net/browse/CLS-4941) promotion | Complete/Edit iguais; "first change wins" fica até o ajuste com o PO (decisão 7) |

## 3. Sub-task nova proposta

Nenhuma.

## 4. Perguntas que `decisions.md` não responde

1. **Labels de permissão no front.** O AC pede "permission labels translated in all 6 locales" e a
   matriz #65 mostra que os labels da tela ("Execute Offer gift", "Access Gifts tab") estão no front.
   Nenhuma sub-task do front fala disso. Proposta: uma linha na 4943 (marcada acima). Sim ou não?
2. **Compêndio §3.2.** Requisito da spec sem repositório, portanto sem sub-task. Quem atualiza (Francisco?)
   e quando? Só precisa ficar dito; o split não cria nada.
3. **Component da CLS-4936.** Título `{C}`, component `D-Team`, e a tabela dá job-library → Messenger →
   **C**. Se corrigir para C-Team, o union do pai ganha `C-Team` (hoje A, B, D, F). A emenda não toca
   nisso sem o seu "sim".
4. **Label do status `completed` no front.** A página do Dimitris diz "Delivered"
   (`gift_checkout.status.completed`); a 4943 diz "Completed"; a spec não nomeia. Proposta: "Completed" nas
   duas superfícies. Confirma?
5. **Contadores das abas.** A página chama `GET …/gifts/count`; a spec não pede contador. Proposta: sai da
   página (fora do escopo), e nem a 4940 nem a 4942 criam rota de contagem. Confirma?
6. **Adjustment: final ou aberto?** O item 8 do `decisions.md` diz "final" (Lucas), o 8b diz "continua
   aberto só o Adjustment, com o Francisco". A 4944 acima já manda remover. Se ainda depende do Francisco,
   tiro a palavra "Adjustment" da linha e deixo o resto.

Notas sem decisão pendente:

- A 4936 diz "starts from branch CLS-4702"; o `execution.md` diz `origin/master`. `gift_canceled` não está
  no master do job-library (só em `origin/CLS-4702`). Não muda com a spec, então não entra na emenda; vale
  conferir no plano da 4936.
- O título do pai ("…complete gifts to order") ficou velho; o split não edita o pai além de components e
  label.

## O que será escrito no "sim"

- `editJiraIssue` em 4 sub-tasks existentes (4940, 4942, 4943, 4944): summary e description. Sem mudar
  points, component, repositório, labels, assignee ou status.
- 0 sub-tasks criadas, 0 links `Blocks` novos.
- Pai: components = union das sub-tasks, hoje `{A-Team, B-Team, D-Team, F-Team}` (igual ao atual; vira
  `+C-Team` se a pergunta 3 for sim); labels `sdd-split` já presente, nada a acrescentar. Status
  **Backlog → Split** (transição 2): o skill faz isso na mesma aprovação, porque o pai está em Backlog.
- Comentário de custo do `sdd-split` no pai (passo 20 do skill).
- Toda sub-task segue com exatamente um repositório; nenhuma de teste, deploy, Team O ou QA.

---
name: cls-3734-schedule-not-started-expedite
description: "CLS-3734 expedite (celesta-promotion PR #554) — 500 na lista do jogador antes da primeira ocorrência; regra de produto decidida com o Francisco e pendência de reativar a config 382 em prod-1"
metadata:
  node_type: memory
  type: project
  originSessionId: 2b3f486e-22c5-45db-b616-ca62025ae719
  modified: 2026-10-16T07:55:28.973Z
---

# CLS-3734 — lista do jogador dava 500 antes da primeira ocorrência (expedite, 2026-10-15)

**Bug:** config com limite por jogador + escopo por ocorrência + primeira ocorrência no futuro. O
`RecurrAdapter::getUpdatedAfter` procurava ocorrência atual ou anterior, não achava e lançava
`RuntimeException` — derrubava a lista inteira do jogador (502 no gateway) e o promo code. Config 382
"[PROMO CODE] PAYDAY AUTOMATIC", domínio 53, prod-1, ~190 erros em 2026-10-14.

**O que o Bohdan tinha feito (PR #554 original):** trocou o 500 por **esconder** a promoção até
começar. Rejeitado: o Francisco quer ver a promoção futura ("we want to promote the promotion before
it starts"), e global/sem limite já apareciam — ficava inconsistente.

**Regra de produto (confirmada com o Francisco, 2026-10-15 13:39):** data a partir da qual os prêmios
são contados para o limite por jogador, escopo ocorrência:
- dentro da ocorrência: início dela (igual a antes);
- entre ocorrências: **fim da anterior** — quem atingiu o limite volta a ver "assim que termina";
- antes da primeira: início da primeira (não "criação", para não contar prêmio de schedule antigo
  editado);
- depois da última: início da última (igual a antes).

Mudança visível fora do bug: no promo code entre ocorrências, quem atingiu o limite agora recebe
"calendar not active" em vez de "limit reached".

**Estado:** fix pushado em `hotfix-schedule-occurrence` (commit e695523bd + merge do master), suíte
verde, CI verde, Proteus rodou `playerPromotionConfigurations.pcpr-4` e `promotionSchedules.pcpr-9`.
Francisco validou em preprod com a config 448 (8 checks ✅). Ticket "In preprod".

**Release e verificação em prod-1 (2026-10-16):** PR #554 mergeado 06:32 UTC, release `v1.375`.
A config 382 foi reativada **antes do rollout terminar**: 3 erros na `v1.374` às 06:37-06:39 UTC
(jogadores 2274829 ×2 e 2133805, domínio 53). Depois disso zero erros no fingerprint
`v12.AB6321C70365CC98C858F5FDAD604482`; às 07:53 UTC só `v1.375` servia o endpoint, tudo 200.
Ticket verificado em prod-1.

**Pendente (não bloqueia):**
- descrição do PR #554 estava vazia no merge (texto proposto na sessão de 2026-10-15);
- cenário behat inverso "some depois de ganhar na ocorrência atual" não existe na lista.

Pré-existente, não corrigido: schedule de ocorrência única com `startsAt` com segundos ≠ 0 ainda dá
500 na janela entre o início e o minuto seguinte (`getCurrentOccurrence` arredonda, `getNextOccurrence`
não).

Relacionado: [[project_proteus_pr_procedure]] (Proteus verde com 12 suítes mutadas).

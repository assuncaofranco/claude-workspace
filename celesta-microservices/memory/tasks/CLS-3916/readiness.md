---
name: cls3916-readiness
description: "CLS-3916 (gift como prêmio de promoção) — avaliação de prontidão em 2026-11-16, lacunas do split e perguntas abertas"
metadata:
  node_type: memory
  type: project
  originSessionId: 8c7cc2c5-c69c-4bdb-8e29-7c156d2905fb
  modified: 2026-11-16T10:28:19.092Z
---

Avaliação em 2026-11-16, com a Story em Split e 10 sub-tasks (4767–4776), nenhuma com branch ou plano. O front (4776, Dimitris) já está em In Progress, embora esteja bloqueado pelo BO 4774.

Lacunas que o split não cobre:
- A promotion não tem rota de messenger para `UserActivityJob` (só backoffice, notification e statistics_kpi). O 4772 passa a produzir `gift_offered`, então precisa de transport, fila, env e IAM. Pode virar request para o time O.
- `RewardHandler::issuePlayerBonuses` (Standard, l.206) retorna cedo quando o player não tem moeda e manda toda reward com config para `offerForPromotionReward`. O gift precisa sair desse loop.
- No `GiftController::resolveIdempotencyKeyRaceWinner`, o SQL cru lê `source_user_id` e `source_scenario_id`. Precisa migrar no 4770, antes do drop do 4773.
- Hoje a promotion recusa config de gift como reward (`RewardSubscriber` l.99). Esse é o portão até o 4771.

Dependências abertas:
- O CLS-3316 (motivo de oferta nas configs) bloqueia a Story e está em Split. A config de gift só tem o `reason` string antigo; o gift tem os dois (`reason` e `reason_id`).
- O CLS-3865 (Gifts to order) está em Split e não tem link com a Story, mas o AC cita esse ticket.

Perguntas: para o PO, qual motivo copiar, se o ticket espera o 3865 e onde o operador vê o gift pulado. Para o Marcello, se a entidade `Source` (4770 e 4773) compensa o custo, comparada a uma coluna `source_promotion_id`.

**Atualização de 2026-11-16, 10:30.** As perguntas foram postadas no Jira com menção: no CLS-3916 (comentário 92818), cinco ao PO e a da `Source` ao Marcello; no CLS-3316 (comentário 92819), a sub-task do celesta-scenario. A questão do motivo saiu da lista: o CLS-4743 dá `reasonId` à config de gift, e o gift copia esse valor. Os planos do 4767 (#635), do 4768 (#561) e do 4769 (#525) estão em PR e em Planned. A matriz, as decisões e a pendência do manifesto (o 4771 e o 4772 vão no mesmo deploy) estão em `tickets/CLS-3916/`.

Relacionado: [[cls4163-gift-reasons]], [[cls419-gift-emitter]]

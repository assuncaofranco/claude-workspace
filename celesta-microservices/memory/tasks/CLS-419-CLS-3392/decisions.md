---
name: cls419-cls3392-decisions
description: "CLS-3392 (promotion emite GiftEventJob para o statistics) — escopo decidido em 2026-10-07: só o emissor, replay fora"
metadata:
  node_type: memory
  type: project
  originSessionId: de2ded7e-3709-447d-936b-9fc32bb2c8c8
  modified: 2026-10-08T13:01:28.983Z
---

# CLS-419 / CLS-3392 — promotion emite KPI de gift

Pai CLS-419: generosity em tempo real vinda do statistics, não do BigQuery.

**Escopo (Lucas, 2026-10-07): só o emissor.** Despachar `GiftEventJob` no `POST /player/{playerId}/gift`
(`GiftController::postGift`), único ponto onde gift nasce; gift só tem status `claimed`.

**Replay fora.** Só o plano do CLS-3433 (job-library, do indover) atribui "emitter and replay command"
ao 3392; nem o 3392 nem o pai pedem. **Why:** ticket de outro time, quem escreveu o nosso não pediu, e
não cabe a nós decidir backfill. **How to apply:** não implementar nem abrir discussão; se perguntarem,
a resposta é que não foi pedido.

Fatos de implementação:
- Job em `dev-CLS-419-CLS-3433` até a tag (prevista v3.134).
- `eventType`: `created` na oferta (`previousStatus` null); `status_changed` não ocorre hoje.
- `amount` DECIMAL→float; `currency` já é length 3 (UST); datas `Y-m-d H:i:s`, ambas = `created_at`.
- Promotion não tem fila `statistics-kpi`: falta parâmetro, transport e routing (wallet usa `SQS_QUEUE_PREFIX`).
- Deploy: statistics antes do promotion (consumer velho descarta a classe).
- `eventType` = `Lancaster\Constants\Statistics\EventTypeConstants` (compartilhada, já existia).
- **Edição incluída (Lucas, 2026-10-07):** subscriber Doctrine (`AbstractCRUDJobEmittingSubscriber`) emite no insert e no update **só se `status` mudou**; hoje nenhum caminho muda status, fica pronto. Edição de outros campos é problema de quem criar.
- Falha de envio após a resposta = N: padrão de todo emissor do statistics (`PostResponseMessageDispatcher`, sem retry no produtor).
- Coleção em `sdd/_how_to_test/CLS-419-CLS-3392/` (2026-10-08): BO domínio 1 / player 1 (EUR, sem USD); statistics na `CLS-419-CLS-3353-api` (indover fez force-push em 08/10: tabela virou `event_promotion_transaction`, comando `kpi:process-events promotion`; job inalterado). Antes do emissor: 7/9 asserções, só o KPI final falha (esperado).
- Statistics dev: o `install.sh` monta o banco com `schema:update`, **não** migrations; `migrate` quebra em 2021. A linha `generosity` da `kpi_formula` não existe em dev (só a migration insere).
- **Implementado 2026-10-08, não commitado:** `GiftEventSubscriber` + messenger + behat/unit. Suíte 1591/1591 + 1006/1006, Newman 9/9, linha no statistics confere com o gift. Lint 100 (`{@inheritDoc}` no `createJob`; dispatcher via `services.yml`).
- Job-library mudou duas vezes em 08/10; versão final `4891e64`: **sem** `sourceUserId`/`sourceScenarioId` (decisão TL + PO). Consumer: tabela `event_promotion`.
- **Review independente (08/10) pegou:** transport tem que ser a conta **quanta** (é onde o statistics lê; em prod-1 a kubernetes é outra conta e a mensagem se perderia) e `created`/`status_changed` já existiam em `celesta-constants` `Statistics\EventTypeConstants` — eu tinha afirmado que não. Ambos corrigidos.
- **PR promotion #547 aberto (2026-10-08)**, commit `59bfdeb34`, sem atribuição. Consumer = statistics #1009. Deploy: statistics antes do promotion (consumer velho apaga a mensagem); pendente confirmar com DevOps `sqs:SendMessage` da chave quanta do promotion em `statistics-kpi`. Instruções em `claude-workspace/celesta-microservices/tickets/CLS-419-CLS-3392/deployment-instructions.md`. **Estado fim de 08/10:** #547 enviado para review; teste em pp1 adiado (CI do statistics #1009 do time A falhando). Pendentes: preprod-1 (células #1 e #2 pelo BO + leitura do `event_promotion` via kubectl), trocar composer para `^3.134` após merge do job-library #538, confirmar SendMessage da chave quanta.
- Spec/plano em `sdd/_specs|_plans/CLS-419-CLS-3392.md`, branch local criada a partir de master, nada commitado.

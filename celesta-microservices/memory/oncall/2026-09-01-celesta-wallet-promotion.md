---
name: oncall_2026-09-01_wallet_promotion_missing_bonus
description: "Healthcheck 089 (wallet sub_balance de bonus sem bonus em promotion) — 10 ids em prod; identidade CEL-6848, os 3 scripts que participam do dual-write e os 4 mecanismos de perda silenciosa do delta"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9ea21bde-6846-4879-8d74-421e91a924ce
  modified: 2026-09-01T10:29:44.015Z
---

## Alerta
Healthcheck Dagster `089_exists_wallet_recent_bonus_sub_balance_ids_in_089_promotion_bonus_existence_lookup` — 10 `sub_balance` (discr=bonus) recentes em prod sem `bonus` correspondente em celesta-promotion: 35684240, 35684266, 35684304, 35683883, 35683885, 35683900, 35684283, 35684210, 35682343, 35683279.

## Os 3 scripts do dual-write (celesta-scripts) — nenhum deles é óbvio pelo código dos serviços
1. **`script/CEL-6848/MigrateBonusDataToPromotion.php`** — forward sync wallet → promotion. `promotion.bonus.id` **é sempre** `wallet.sub_balance.id` (linha 88): insere com id explícito (`--stop-auto-increment` derruba o AUTO_INCREMENT no backfill e restaura em `MAX(id)+1`). É por isso que o healthcheck compara ids 1:1.
2. **`script/CLS-2074/BackfillSubBalanceBonusData.php`** — sweep periódico no wallet com `UPDATE sub_balance t LEFT JOIN bonus_model bm SET t.bonus_id = t.id, t.reward_type = COALESCE(bm.type, t.reward_type)`, cursor por tabela + `CURSOR_OVERLAP = 10000`. Roda em `sub_balance` e `archive_sub_balance`.
3. **`script/CLS-1714/CheckWalletPromotionSync.php`** — HC3, diário às 00:01, janela de **ontem**. Trata "existe só num lado" como contagem **informativa, não falha** (integridade referencial é do HC1). O 089 é o outro check, sobre linhas *recentes* — por isso ele necessariamente pega linhas que o delta ainda não alcançou.

## Armadilha de diagnóstico (errei nela nesta sessão)
`sub_balance.bonus_id = id` **não prova nada sobre o promotion**. No código do wallet o único `setBonusId()` é o `ClaimHandler` (claim postado pelo promotion), o que sugere fortemente que só o fluxo via promotion preenche o campo. É falso: o script CLS-2074 estampa `bonus_id = id` em toda linha nova via SQL cru, fora do Doctrine. Antes de inferir origem por um campo, procurar writers em **celesta-scripts**, não só nos `src/` dos serviços.

Corolário útil: esse UPDATE é SQL cru e `sub_balance.updated_at` é `Gedmo\Timestampable(on: 'update')` sem `ON UPDATE CURRENT_TIMESTAMP` no DDL — então o backfill **não** mexe em `updated_at`, não reativa o delta e não embaralha a watermark.

`claimed_at` também não indica origem: o `BonusListener` do wallet grava nativamente (`onFlush`, inserção e update OFFERED→CLAIMED, quando `bonusModel !== null`), e o `ClaimHandler` grava a partir do payload do promotion.

## Flag `move_bonus_to_promotion` — OFF desde junho
`flips` (base `flipper`) tem só `id, name, status` — **sem timestamp**. Nenhum dos 4 `FlipperClient` (promotion, wallet, backoffice, scripts) escreve nela: a flag é virada **manualmente**, fora dos microserviços, sem trilha de auditoria nossa.

Verificado em 2026-09-01 via `information_schema.tables`: `flips.update_time = 2026-06-24 10:29:07`, `flip_actors` com `update_time` NULL e `auto_increment = 1` (vazia — nunca houve rollout por domain). Ou seja **status=0 desde junho**: promotion nunca foi autoritativo, `RewardOfferService::offerReward()` e `RewardClaimService::claimOne()` sempre retornaram null, e o forward sync sempre rodou.

**Como consultar histórico de uma tabela quase imutável sem coluna de timestamp:** `SELECT create_time, update_time, auto_increment FROM information_schema.tables` — o `update_time` do InnoDB dá a última escrita (ressalvas: só a última, é por tabela, e vira NULL se a instância reiniciar). `id` fora de ordem vs. as outras linhas denuncia delete+recreate. Quem/valor anterior só com Aurora Advanced Auditing (`server_audit_logging` → CloudWatch) ou binlog com retenção já configurada antes da mudança.

## Diagnóstico: a watermark separa perda de atraso
Delta = `updated_at >= watermark AND updated_at <= NOW()-5s`, ordenado por `(updated_at, id)`, watermark em `promotion.registry.sync_bonus_updated_at`, avançando **por batch commitado**. Skip dentro de batch que commita ⇒ linha nunca revisitada, a não ser que o `updated_at` mexa de novo.

Estado lido: watermark `2026-09-01 10:00:14`, `migrate_bonus_backfill_done=1`, `migrate_bonus_max_id=migrate_bonus_last_id=35466641` (os 10 ids estão **acima** do ceiling → nunca passaram pelo backfill, dependem só do delta).

- **abaixo da watermark = lido e descartado**: 35682343 (09:31:41, claimed), 35684210 (09:54:47, claimed), 35684240 (09:11:51, **canceled**), 35684266 (09:18:06, **canceled**), 35684283 (09:58:26, claimed)
- **acima = só atraso**, entram no próximo run: 35683883, 35683279, 35683885, 35683900, 35684304

Dos 5 descartados, os 2 `canceled` são **perda permanente** (status terminal ⇒ `updated_at` nunca mexe mais). Os 3 `claimed` devem se curar sozinhos no próximo bump de `updated_at` (wagering, expiry).

## 4 mecanismos de perda no delta
1. `null_bonus_model_id`
2. `bonus_model_not_migrated` — `bonus_model_id` sem `reward_configuration`
3. `player_unresolved:<pid>` — player ausente do memberzone ou `domain_id`/`currency` inválido (`ensurePlayersExist()`: *"their bonuses will be skipped"*)
4. `SYNC_SAFETY_LAG_SECONDS = 5` — `updated_at` vem do clock PHP no flush, não do commit; request que demore >5s entre flush e commit cai abaixo da watermark sem nunca ter sido visível

1-3 vão pro CSV `celesta-scripts/data/cel-6848-skipped-bonuses.log` (`sub_balance_id,bonus_model_id,reason`). O 4 não é logado em lugar nenhum — se os ids **não** estiverem no log, é ele.

## Status
Decisão: REPORTAR E ESPERAR. Dinheiro no wallet correto nos 10; wallet é a fonte da verdade com a flag off; upsert do delta é idempotente, então o resync das 2 terminais é correção de horário comercial. Nenhuma escrita em prod feita.

Pendente: ler o skip log pros 5 abaixo da watermark; resync das 2 canceled; e ticket para o descarte silencioso (batch commita e watermark passa por cima da linha pulada) — esse é o problema estrutural, não as 10 linhas.

Relacionado: [[project_cls2450_cls2452_duplicate_subbalance_investigation]], [[project_missing_bonus_model_investigation]].

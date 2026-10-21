# 2026-10-02 — celesta-etl, BI Latency above 20 Minutes (Prod-1)

Dois incidentes P2, 22:43 e 22:46 UTC-local do Lucas: `resource_name:reward_bonus` e `resource_name:segment_player`. Os mesmos dois dispararam em 2026-10-01 (22:41 e 23:07) e resolveram sozinhos.

**Balde:** ruído conhecido. ETL/BI, não toca dinheiro nem jogador; o run completa, nada se perde.

**Causa:**
- `reward_bonus`: confirmada na thread de 2026-10-01 (Ivan Horbushko). O sync recarrega a tabela inteira a cada run, porque a tabela do BQ é um join de `bonus` com `reward_bonus_configuration`. O tempo cresce com o volume e passou de ~20 para ~21 min. A correção é o CLS-3113: tabelas `promotion_*` com sync incremental, e os operadores migram para as MVs `_v1` novas.
- `segment_player`: **não confirmada**. Ninguém explicou na thread, e o CLS-3113 não cobre (ele só trata as tabelas de promotion).

**Saída:** reportar e esperar.

**Recorrência:** `segment_player` disparou de novo em 2026-10-03 às 23:42, a terceira noite seguida.

**2026-10-04, causa do `segment_player` confirmada no código** (`celesta-etl` @ `bb625bd7`):
- Também recarrega a tabela inteira (`bqmode = "truncate"`, leitura a partir do id 0).
- O limite do job é `JOB_TIMEOUTS_SECONDS["segment_segment_player"] = 1140` em `src/etl/triggers.py:102` (Ivan Demenkov, 2026-04-17), e o cron é `*/20`.
- **Parte** das execuções é morta pelo Dagster (`DagsterExecutionInterruptedError`, em ~19m12s). Disparou também o monitor "BI error rate breached 3.0" (21:02 e 22:01).
- **Correção do meu primeiro diagnóstico:** eu disse que toda execução morria e que a tabela estava parada desde 20:39, e a UI do Dagster desmentiu. As execuções de 21:20 (1h08) e 21:40 (45 min) terminaram com sucesso, então a falha é intermitente. As execuções levam a tag `etl/table_lock` e parecem fazer fila umas atrás das outras. Hipótese não confirmada: a "Duration" da UI conta a espera na fila e o `max_runtime` não. **Olhar a UI do Dagster antes de concluir pelos spans do APM.**
- A tabela `segment_player` do BigQuery atualiza com atraso, mas não fica parada. Nada se perde na origem.

**2026-10-05, mecanismo confirmado pelo log e pela lista de execuções do Dagster:**
1. O `max_runtime` (1140 s) manda cancelar ("Sending run termination request"), mas o `RetryPolicy(max_retries=3)` do op captura o `DagsterExecutionInterruptedError` como `RetryRequested`, e a execução continua com um novo "attempt". **O cancelamento não mata a execução.** Por isso existem execuções de 45 min a 1h08 com Success, e uma execução que aparecia como Failure vira Success depois.
2. Com o cron `*/20`, as execuções se sobrepõem: três ao mesmo tempo por volta das 22:00. A tag `etl/table_lock` não impede isso.
3. Todas usam a mesma tabela temporária, `global.temp_segment_player`. Prova: a execução de 23:20 terminou às 00:19:42, e a de 00:00 falhou às 00:19:56 com "Not found: Table celesta-325419:global.temp_segment_player".
4. **Risco:** a `segment_player` do BigQuery pode ficar inconsistente, não só atrasada. Uma execução limpa e sozinha corrige.
- **Não reexecutar à mão:** aumenta a colisão.
- **Para o time de ETL:** retry contra `max_runtime`, o lock, o nome da tabela temporária por execução e a recarga completa da tabela (CLS-3113).
- **Correção, do time de ETL:** subir o limite junto com o espaçamento do cron, ou sync incremental (o caminho do CLS-3113).
- O monitor de lentidão exclui `resource_name:bonus`, mas não o `reward_bonus`.

**Checar no dia útil:** se `segment_player` também faz recarregamento completo e se precisa de ticket próprio. Enquanto o CLS-3113 não sai, o `reward_bonus` vai disparar toda noite.

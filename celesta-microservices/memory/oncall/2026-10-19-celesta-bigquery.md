# 2026-10-19 — celesta-bigquery, Big Query scheduled query failed (Celesta)

Monitor 120237871 (time BI, criado por Randy Martin em 2026-08-31). É **P4 no Datadog**, mas o PagerDuty abriu como **P1**: o roteamento não respeita a prioridade do monitor.

Query do monitor: `sum(last_1h):sum:gcp.bigquerydatatransfer.transfer_config.completed_runs{gcp-account:celesta,completion_state:fail*} by {completion_state,status,config_id} > 0`. É métrica do GCP; não tem log no Datadog. O `{{config_id.name}}` da mensagem sai vazio, então o nome da query não aparece.

**Alerta:** config `6aad1f51-0000-2248-84d2-089e0824144c`, `completion_state:failed`, `status:unavailable`, disparou às 23:00:31 UTC.

**Evidência:** a query roda de hora em hora, e todas as execuções de 16/10 a 19/10 foram `succeeded,ok`. Só uma falhou.

**Balde:** dependência externa, **não confirmada**. A outra query que rodou na mesma janela, a `68807915` (`player_kpi`, a cada 15 min), passou em todas as execuções em volta do horário da falha. Então não houve queda geral do BQ: o `UNAVAILABLE` caiu só nesta execução. É provavelmente transitório, mas é palpite até o BI ler a mensagem de erro. Não toca dinheiro nem jogador.

Para separar "falha geral do GCP" de "falha desta query" sem acesso ao GCP: `completed_runs{gcp-account:celesta} by {config_id,completion_state,status}` na janela da falha.

**Disparo anterior:** 2026-10-01 11:23 UTC, outro config (`68807915…`), `status:unauthenticated`. Recuperou em 1h.

**Saída:** reportar e esperar.

**Resultado:** a execução seguinte passou (`succeeded,ok`) e o monitor recuperou sozinho. Conferido na métrica, não só pelo resolved: o monitor também fecha quando a última hora passa sem falha, o que pode acontecer só porque o tempo andou.

**Desfecho, 2026-10-20 08:41 (Ivan Demenkov, BI):** a `6aad1f51` atualiza a tabela de **bônus**. "No damage, just bonus table was not updated in this hour": a execução seguinte cobriu tudo e não precisou de backfill. O Virgile perguntou de manhã "what are the damages / anything to recover", que era justamente o que o oncall não conseguia responder sem acesso. Por isso o Lucas pediu na thread acesso de leitura à configuração das scheduled queries.

**As 6 scheduled queries do `celesta-325419`** (console, 2026-10-20; horários em UTC, região europe):
- `player_kpi`: a cada 15 min (= `68807915`)
- `bonus`: de hora em hora, :50, de 00:50 a 23:50 (= `6aad1f51`)
- `player_kpi_eod`: a cada 30 min, entre 00:00 e 01:00
- `player_kpi_sum`: todo dia, 02:10
- `celesta_backup`: domingo, 01:10
- `player_kpi_eow`: segunda, 01:10

O config_id das outras quatro ainda não foi conferido. Erro meu na noite do incidente: concluí "só existem duas" a partir de uma janela de 5h no Datadog, quando eram só as duas que rodam nessa janela. A métrica só mostra queries que rodaram no período consultado. O console mostra o horário em UTC+1.

**Buraco de acesso (resolvido em 2026-10-20: o Lucas agora vê as scheduled queries no console):** o Lucas vê o projeto `celesta-325419` no console, mas não tem `bigquery.transfers.get`, então não abre Scheduled queries nem o run history. Também não tem `gcloud` instalado. A mensagem de erro e o nome da query ficam com o BI.

**Checar no dia útil:**
- resposta do Virgile sobre o acesso do oncall ao BQ;
- por que o PD trata um P4 como P1.

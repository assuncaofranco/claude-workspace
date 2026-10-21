# 2026-10-05 — Celesta Rundeck Error on Job, terminate_long-running_mongodb_operations

Alerta P2 às 06:07. O job "Terminate Long-Running MongoDB Operations" (projeto Activity, `jobs/prod-1/Activity/terminate_log_running_mongodb_operations.yaml` em `celesta-rundeck`) roda **a cada minuto**, com limite de 30 s, e mata operações com mais de 25 s no DocumentDB `celesta-prod-1-documentdb` (banco `activity`).

**Balde:** ruído conhecido. Uma execução isolada falhou (`#32810034`, 06:04, em 0 s, então não foi por tempo limite; provavelmente o `mongosh` não conectou). As execuções antes e depois estão verdes.

**Monitor:** soma os erros das últimas 6h e dispara com 1 ou mais. Por isso o alerta fica vermelho por 6h depois de uma falha isolada. Uma falha anterior parecida foi atribuída pelo Ivan Horbushko a um resync dele, que gerou operações longas.

**Saída:** reportar, sem ação. Não reexecutar: o job já roda a cada minuto.

**Só vira problema se:** houver falhas seguidas, porque aí as operações longas do activity não são mortas.

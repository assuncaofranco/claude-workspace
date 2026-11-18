---
name: celesta-segment-rds-blue-green
description: "Quando sugerir subir a classe do RDS do segment via Blue/Green, e como o Ghislain fez em 06/11 (parâmetros do CloudTrail, tempos, armadilha dos drains presos na antiga)"
metadata:
  node_type: memory
  type: reference
  originSessionId: 1a8e9ad7-6709-4025-814c-1806b867af7b
  modified: 2026-11-07T23:46:52.296Z
---

Incidente de origem: [[oncall-2026-11-06-celesta-segment-rds]]. Foi a mudança de classe que tirou a pressão; o PR #843 (1 drain por host) não tinha sido deployado.

## Quando sugerir

Todos juntos:
- CPU do RDS > 80% **sustentada**, subindo junto com o tráfego (não é spike de um job).
- Limitada por CPU: read IOPS ~0, conexões estáveis, latência de leitura/escrita normal (1–6 ms).
- Performance Insights com carga (AAS) acima do número de vCPUs (06/11: 3.9 de média e 5.3 no pico, em 2 vCPU).
- A carga vem de quem precisa rodar: cortar workers só move o backlog para a SQS (06/11: com 3 hosts, a `segment-balance.fifo` chegou a 31 min).
- t4g em modo unlimited com crédito zerado (não estrangula, mas cobra).

Não é Blue/Green quando: query nova depois de deploy (rollback), job descontrolado (matar), memória (ver o caso do scenario, performance_schema), conexões esgotadas.

A decisão e a execução são do SRE. Ghislain fez pelo console como **root** da conta `413101478321`; não sei se o perfil `celesta-prod-1` tem permissão.

## Como foi feito (CloudTrail, 06/11)

1. **Create** (`CreateBlueGreenDeployment`, 20:19:56 UTC). Console: RDS → a instância → Actions → Create Blue/Green deployment.
   - source `celesta-prod-1-segment`, `targetDBInstanceClass: db.t4g.xlarge`
   - `targetEngineVersion: 8.4.11` (era 8.4.9, minor junto)
   - `targetDBParameterGroupName: celesta-prod-1-segment-mysql-8-4` (o mesmo)
   - `targetStorageType: gp3`, `targetAllocatedStorage: 22`
2. **Esperar `AVAILABLE`**: 47 min (20:19 → 21:06). Réplica por snapshot ~15 min → conversão Multi-AZ ~8 min → upgrade minor ~5 min (downtime só no green) → backup ~3 min. Conferir `ReplicaLag` do green em 0–1 s.
3. **Switchover** (`SwitchoverBlueGreenDeployment`, `switchoverTimeout: 60`, 21:09:53). Escrita parada ~2 s. O green assume o nome; a antiga vira `-old1`, read-only.
4. **Depois da troca, reiniciar os drains na hora**: `worker_player_segment_update` nos hosts do ASG (Rundeck → Commands, filtro `as-segment-worker-i.*`, `cd /home/admin/app && docker compose restart worker_player_segment_update`). Eles seguram conexão aberta e ficam na `-old1` até o `--time-limit=3600`: 06/11 foram ~23k erros/min `1290 --read-only` por 16 min. Os consumers reconectam sozinhos.
5. **Provar**: `DatabaseConnections` da `-old1` = 0 (CloudWatch, 1 min) + nenhum erro `read-only` no Datadog + `segment-failed.fifo` (06/11: 345 mensagens na troca, o Ghislain tratou) + `segment-balance.fifo` em segundos.
6. **Limpeza** (SRE): a `-old1` foi parada, com deletion protection; o objeto do Blue/Green (`bgd-2fl1yxpnes7iamwd`) não foi apagado. RDS religa sozinha uma instância parada depois de 7 dias.

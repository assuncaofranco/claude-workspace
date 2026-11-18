---
name: 2026-11-11-celesta-game-latency
description: "game prod-1 p50 subiu de patamar em 2026-11-05 08:00–08:40 UTC (webhook 210→250 ms), junto com CEL-9700 (ALB cutover) e CEL-9372 (pod sizing do cluster); réplicas do game e dependências iguais; suspeita = nodes mais densos. O alerta de 11/11 20:01 é só o pico de 2 min em cima da base nova"
metadata:
  node_type: memory
  type: project
  originSessionId: 38f81419-1064-4b7b-b648-11573433d27e
  modified: 2026-11-12T07:45:47.124Z
---

**Alerta:** `[prod-1] celesta-game | Symfony request p50 latency > 290ms in 15m` (monitor 18239765, P2).
Disparou 2026-11-11 20:01:05 UTC, resolveu 20:02:05. Pico de 2 min na virada da hora, só no
`webhook_transactions_action`. Na hora classifiquei como ruído; no dia seguinte o Janis apontou no Slack
que a base subiu de 210 para 250 ms, e o pico era só a ponta disso.

**Degrau de base, confirmado:** `webhook_transactions_action` p50 diurno 205–225 ms até 04/11, 244–252 ms
todo dia desde 05/11. Serviço todo 175–185 → 205–215 ms. Em hora: 07:50 = 203, 08:30 = 256, e fica.

**Coincide com (05/11, #sre-b2b-celesta, Lucas Azevedo):**
- 08:09 CEL-9700 #3139, ingresses do ALB para Services fixos; 08:18 #3140, preStop ≥ 15 s, todos os apps
  redeployados.
- 08:34 CEL-9372 #3142 (`df0991441ba` no celesta-argocd): requests de CPU/memória pelo uso de 14 dias,
  HPAs só por CPU, mínimos menores. Cluster de 373 para 190 pods.

**O que não é:**
- código do game: v1.832 só entrou às 09h, o degrau é às 08h com a v1.831;
- dependência: banco, Redis e HTTP com a mesma mediana antes e depois (spans indexados, 04/11 × 05/11
  10–16 UTC). O tempo a mais é self time no PHP;
- réplicas do game: `kubernetes_state.hpa.current_replicas{horizontalpodautoscaler:game}` igual
  (~12–17 de dia). O CEL-9372 não mexeu no request do php-fpm (0,3) nem no min (4); trocou o HPA para
  `ContainerResource` no `game-phpfpm` e pôs `scaleUp.stabilizationWindowSeconds: 120`;
- throttling: zero, o php-fpm não tem limit.

**Suspeita, não provada:** nodes mais densos. Nodes de dia ~19,5 → ~17,5, CPU user máx por node
50 → 55%. O game tem request 0,3 e nenhum limit; os vizinhos agora reservam menos e disputam mais CPU.
Confirmar no kube: vizinhos dos pods do game e CPU dos nodes onde eles rodam.

Gotcha: `kubernetes_state.container.running` por `kube_deployment:game` soma o preview do blue/green e
deu "pods caíram pela metade". Falso. Contar réplica pelo HPA. No Datadog, prod-1 é
`kube_cluster_name:celesta-prod-1-cluster` e não existe tag `kube_namespace`.

**Saída:** reportar. Sem erro, +30–40 ms no p50. É do DevOps (CEL-9372). O monitor (limiar 290 ms) ficou
com ~40 ms de folga sobre a base nova.

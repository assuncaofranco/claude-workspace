---
name: 2026-10-17-celesta-game-go
description: "madrugada 2026-10-17, game e game-go lentos só na eu-west-1a em loop; causa = PreferClose (CEL-9484, 16/10) concentrando tráfego nos 2 pods da wallet da 1a + descheduler LowNodeUtilization despejando esses pods a cada 3 min; hotfix = suspender o descheduler via celesta-argocd"
metadata:
  node_type: memory
  type: project
  originSessionId: c8554bb9-a9ca-41c3-a180-6ebb1e1446c9
  modified: 2026-10-17T02:43:18.174Z
---

**Alertas** (00:40–03:00 BST, #celesta-alarms-prod-1, em loop): `Celesta Game-Go TG ELB above 120ms`,
`Celesta Game TG ELB above 225ms`, PD `Celesta Game Go has latency above 95ms` (P2).

**Balde:** nenhum dos cinco. Mudança de infra do dia anterior (CEL-9484) em conflito com um componente
antigo (descheduler). **Causa raiz confirmada.**

Cadeia:
1. 16/10 10:46 BST, CEL-9484 (Lucas Azevedo, celesta-argocd): `trafficDistribution: PreferClose` nos
   Services de prod-1 de wallet, game, statistics, cms e fluentbit.
2. À noite o tráfego cai, HPA e cluster-autoscaler encolhem; sobram 2 pods da wallet na eu-west-1a.
3. Com PreferClose, todo o tráfego de wallet originado na 1a (game, game-go) cai nesses 2 pods:
   ~3,5 cores cada, node a 95–98% CPU. Os pods de 1b/1c ficam a ~1 core.
4. O descheduler (CronJob `descheduler-cronjob`, kube-system, roda a cada minuto, 597 dias de idade,
   `LowNodeUtilization` thresholds cpu 35/70 por métrica real, `minPodAge: 3m`, `nodeFit: true`) vê o
   node >70% e despeja o pod da wallet assim que ele completa 3 min. O scheduler decide pelo request,
   não pelo uso, e recoloca na 1a. O pod novo sobe frio e pega toda a carga de novo. Loop.
   Logs no Datadog (`service:descheduler "Evicted pod"`): antes de 16/10 13:00 UTC, 0–5 despejos de
   wallet por hora em ~40; desde 16/10 22:00 UTC, **100% dos despejos são da wallet** (37/37, 33/33…).
5. ALB `target_response_time.p50` só na 1a: game 750 ms, game-go 640 ms (1b/1c ~70–105 ms).
   Entre 01:00 e 01:30 UTC pareceu resolver sozinho (HPA 8→10, novos na 1a, 4 pods dividindo) — era
   só uma pausa: `nodeFit` impedia despejo enquanto não havia node com espaço; o autoscaler subiu
   nodes e o loop recomeçou.

Pistas descartadas: tráfego (25–80% **abaixo** da sexta anterior), erros do `quanta.debit`
(`Not sufficient funds`, regra de negócio), 88 queries num trace (~50 ms), NAT gateway, RDS do game,
mysql/redis/SQS do game-go, versão, upgrade de nodes (os `NotReady,SchedulingDisabled` eram
scale-down normal).

**Correção aplicada à mão (sábado ~03:30 BST, Lucas executou):** Lucas não tem push no
`celesta-argocd` (`permissions.push: false`), então o commit `e1dd2af` (remove o patch do PreferClose
só da wallet em prod-1) ficou na branch **local** `hotfix-wallet-drop-preferclose-prod-1` em
`~/Desktop/infra/celesta-argocd`, sem push. O app `wallet` é filho do app-of-apps `celesta` (37 apps,
selfHeal), então:
1. `patch application celesta` → `syncPolicy.automated: null`
2. `patch application wallet` → `syncPolicy.automated: null`
3. `patch svc wallet-active` → remove `/spec/trafficDistribution`
Os 37 filhos mantêm o auto-sync deles; só a wallet fica fora do GitOps.
**Resultado confirmado 02:42 UTC:** zero despejos do descheduler, CPU da wallet espalhada (máx 1,7 core),
HPA 63%/70% com 8 pods, game-go p50 55–81 ms em todos os hosts, inclusive os 4 da 1a (antes 330–510 ms).

**Segunda, nesta ordem:** DevOps mergeia `e1dd2af` → depois religar `automated: {prune: true, selfHeal: true}`
na wallet e no `celesta`. Religar antes do merge traz o PreferClose de volta e o loop recomeça.

Alternativa descartada: suspender o descheduler (stash na branch `hotfix-suspend-descheduler-prod-1`).
Parava o loop mas não a concentração de tráfego.

Como achar rápido da próxima vez: `aws.applicationelb.target_response_time.p50 by {availabilityzone,targetgroup}`
→ se uma AZ só destoa, `kubectl top pods -n celesta --sort-by=cpu`, `get pods -o wide`
(IP 10.11.0–31 = 1a) e `kubectl -n celesta get events | grep Killing` + logs do descheduler.

Gotchas: o game-go não tem span na chamada HTTP pra wallet (`http.DefaultTransport`), o tempo aparece
como self time. A conta 851725549872 não é a de prod. Logs do WAF não chegam ao Datadog (ver Sampled
requests no console). Código 7 da wallet cai como error no `LogWalletFailure` do game-go, significado
não achado por grep.

**Pendente (segunda, DevOps + wallet):** PreferClose × LowNodeUtilization × HPA pela média. Opções:
`topologySpreadConstraints` por zona na wallet, excluir `celesta` do LowNodeUtilization, ou tirar o
PreferClose da wallet. Religar o descheduler depois. Secundário: instrumentar o cliente HTTP da wallet
no game-go.

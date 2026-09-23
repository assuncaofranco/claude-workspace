---
name: oncall_2026-09-04_celesta-game-go
description: "Celesta Game Go traffic dropped to zero — external cause, Quanta's gamelauncher/status down. Recurring issue (2nd known occurrence, different shift), not a Celesta-side fault."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-04T04:04:58.810Z
  originSessionId: 8b76293a-7814-4e3b-be62-bb9725590135
---

## Alerta
`Celesta Game Go Less than 10 hits/sec (Prod-1)` → evoluiu pra `NO DATA`. P1. Também apareceu junto: 2 OOM em pods do ArgoCD (`repo-server`, depois `server`) na mesma madrugada — investigado em paralelo, self-healed, sem ligação confirmada com o game-go.

## Balde
Dependência externa.

## Causa raiz
Endpoint externo `https://vip-prod.quanta.tech/gamelauncher/status` (serviço `game-aggregator`, da Quanta) caiu. Sem sessão de jogo sendo iniciada, zero webhook chega em `celesta-game-go` (`/webhook/quanta/*`). Não é falha do lado Celesta.

**Confirmado, não é suposição:**
- 2-3 sondas sintéticas do Datadog falhando na mesma URL, de localizações diferentes (Paris/AWS, localização privada), 3x seguidas cada.
- Pods do game-go saudáveis o tempo todo: `Running`, 0 restart, CPU ociosa (~0.002) nos 6 pods — confirmado via Freelens, fonte independente do Datadog (ver seção 2 da skill `oncall`).
- APM Traces mostrando `0 spans/s` ao vivo, último trace real minutos antes do alerta.
- Confirmação humana na thread da 1ª ocorrência: "Quanta was down?" → "yes" (Randy Martin/Marcello Duarte).

## Recorrência — 2 ocorrências, turnos diferentes
1ª vez: ~7:18-7:21 (horário comercial do Lucas, não oncall). Thread com a confirmação humana: https://celesta-tech.slack.com/archives/C09HE8NCJ87/p1788493386353889
2ª vez: ~4:41-4:50 madrugada (essa, durante oncall).

Não é padrão de "sempre de madrugada" — é instabilidade recorrente da Quanta em geral, apareceu em dois horários bem diferentes. Vale registrar como fornecedor com histórico de instabilidade, não como padrão de horário.

## Técnica usada, vale repetir
Pra confirmar "pod caiu" vs "não está chegando tráfego real" sem depender do Datadog: lista de pods do Freelens (Running/restart, ambos do Kubernetes) + coluna de CPU (do metrics-server) + Logs do pod. Ficou registrado na skill `oncall.md`, seção 2.

## Resultado
REPORTAR (pra Quanta, não pra Janis — não é fixable do nosso lado). Sem ação de código ou infra do nosso lado.

---
name: oncall_2026-08-29_celesta-segment
description: "SQS Messages Visible above 1k, celesta-segment (segment-balance.fifo) — spike de tráfego, drenou sozinho. Padrão recorrente de dia 29 do mês."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-29T17:36:03.921Z
  originSessionId: 8b76293a-7814-4e3b-be62-bb9725590135
---

## Alerta
`Celesta SQS Messages Visible above 1k (Prod)` — P2, fila `celesta-prod-segment-balance.fifo`, serviço `celesta-segment`. Sábado 29/08, ~17h UTC.

## Balde
Spike / acúmulo de fila.

## Investigação
- Hipótese inicial (errada): consumidor nunca subiu — não existe job de Rundeck nomeado pro `worker_segment_balance_sqs`, e o spec CLS-1809 descreve um rollout em 4 partes (CLS-1809/1811/1813/1810) com um passo manual (CLS-1813) fácil de esquecer.
- Descartada com dados reais: `NumberOfMessagesDeleted` nunca foi zero — milhares/min a janela inteira. `NumberOfMessagesReceived` sobe proporcional. `ApproximateNumberOfMessagesNotVisible` fica estável (worker nunca sufocado). `Visible` sobe ~1h e já começa a drenar.
- Causa real: pico de tráfego (mais jogadores), consumidor absorveu com atraso temporário. Sem perda de dinheiro — é atraso de sincronização de saldo pro segment (CRM/promoção veem saldo desatualizado por um tempo).

## Achado paralelo — não é o causador, mas é real
[WalletBalanceUpdateSubscriber.php](../../../../../Desktop/celesta-projects/celesta-wallet/src/AppBundle/EventListener/Job/WalletBalanceUpdateSubscriber.php) publica toda mudança de saldo real na `segment_balance_sqs` via `TransportNamesStamp`, contornando o `routing:` do messenger.yaml. `docker-compose.prod.yml` define `worker_segment_balance_sqs` com `deploy: replicas: 3` (sintaxe Swarm) — não confirmado se é gerenciado por Rundeck job dedicado ou por deploy de stack único; não investigado a fundo porque não foi a causa deste incidente.

## Recorrência — dia 29 do mês
Mesmo monitor disparou em 29/05/2026 (sexta) — hoje é sábado. **Não é dia da semana, é dia do mês.** Padrão de tráfego diferente (maio: múltiplos picos-e-drenos na mesma janela de 3h, chegando a zerar duas vezes; agosto: uma subida só, suave). Ambos os casos são tráfego, não consumidor morto.

**Hipótese aberta, não confirmada:** algo do calendário financeiro dispara perto do dia 29 (pagamento, bônus mensal, campanha, fechamento). Vale investigar em horário comercial se disparar de novo.

**Dagster descartado como gatilho:** os jobs numerados no Dagster (`001_...` a `029_...`) são majoritariamente healthchecks — leitura/auditoria, não escrevem `Transaction`. Como só transação com status success e mudança de saldo real dispara o `WalletBalanceUpdateSubscriber`, Dagster não é a origem. O próximo lugar a olhar é o que efetivamente grava transação perto do dia 29 — payout, bônus mensal, campanha (payment/promotion), não Dagster.

## Gap de acesso
A fila vive na conta AWS `954607206481` (quanta-aws) — nenhum profile do Lucas (`celesta-prod-1`, `celesta-prod-2`, etc.) alcança essa conta. Só dá pra inspecionar pelo console pessoal dele. Vale resolver isso separadamente — quem está de oncall devia conseguir inspecionar via CLI a fila que o alerta aponta.

## Resultado
REPORTAR E ESPERAR. Sem ação — fila já estava drenando no momento da decisão.

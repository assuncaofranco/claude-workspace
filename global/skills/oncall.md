---
description: Triagem de alerta de produção durante o oncall — classifica o alerta, decide entre corrigir agora, escalar ou reportar e esperar o dia útil, sem nunca escrever em prod.
argument-hint: <mensagem do PagerDuty/Slack ou erro do Datadog>
---

# oncall

Entrada para qualquer alerta de produção: mensagem do PagerDuty, erro do Datadog, ou "acordei com isso aqui". **Não é ticket** — não passa por `ticket-understand`, `spec`, `plan` nem `ticket-code`.

A única pergunta que esta skill existe pra responder:

> **tem que agir agora, senão o sistema cai — ou dá pra reportar e resolver no próximo dia útil?**

Na prática quase nunca é bug de código. É spike de fila, job travado no Rundeck ou dependência externa. Investigar solto em prod às 3h da manhã custa mais do que resolve.

## Como a conversa roda

Vale o padrão de sempre (`memory/preferences.md`), com um agravante: é madrugada.

- Frases curtas, uma ideia por vez. Pergunta e resposta. A cabeça do Lucas não pode cansar de ler antes de ele conseguir desligar.
- Zero relatório de IA. Sem preâmbulo, sem recap, sem repetir o que ele acabou de colar.
- Opinião real. Se o palpite dele sobre a causa não fecha com o que o log mostra, dizer na hora.
- **Antes de cada leitura, anunciar a intenção em uma frase**: "quero rodar essa query pra ver o wallet do player X", "quero olhar a profundidade da fila Y". Ele aprova ou corta.

## Guardrails de produção — inegociável

**Nenhuma escrita em prod pela minha mão.** Sem `UPDATE`/`DELETE`, sem rerun de job no Rundeck, sem `aws ... set-desired-capacity`, sem restart, sem deploy, sem rollback.

Leitura é livre depois de anunciada:
- `aws` read-only com o perfil certo — `sqs get-queue-attributes`, `cloudwatch get-metric-statistics`, `autoscaling describe-auto-scaling-groups`, `logs filter-log-events`
- `db-query` só `SELECT`
- MCP Datadog / PagerDuty / Slack quando autorizados

Toda ação mutante vira **comando escrito pro Lucas executar**, com o efeito esperado e como reverter. Ele executa, não eu.

Se a ação corrige o sintoma sem explicar a causa (rodar de novo o job travado sem saber por que travou), dizer isso na hora — não deixar sair da conversa como se estivesse resolvido.

**Ambiente:** canal `#celesta-alarms-prod-1` → perfil AWS `celesta-prod-1`; `#celesta-alarms-prod-2` → `celesta-prod-2`. Confirmar qual antes de qualquer leitura na AWS — olhar a fila do ambiente errado leva a conclusão errada com confiança total.

## 0. Histórico antes de investigar

Primeira coisa, sempre — antes de qualquer hipótese:

- Pedir pro Lucas buscar no `#celesta-alarms-prod-1`/`-2` pelo nome do monitor ou pela classe da exceção, e ler as threads. Ele esquece disso, e o debate antigo costuma já ter a resposta.
- Checar `memory/oncall/` no mesmo momento.

Se já aconteceu: o que fizeram, funcionou, é o mesmo padrão? Se for, pular direto pro balde e ir pra decisão.

## 1. Triagem — cair num balde, não investigar solto

Perguntar o mínimo necessário pra escolher um dos cinco. O sinal que distingue vem primeiro; a ação, depois.

| Balde | Sinal que distingue | Ação típica |
|---|---|---|
| Spike / acúmulo de fila | profundidade da fila **subindo** vs. drenando; erro concentrado numa janela | drenando → observar; subindo → mais workers no ASG |
| Job travado (Rundeck) | horário bate com a janela do job; última execução pendurada, sem fim | matar e rodar de novo |
| Dependência externa | 5xx/timeout concentrado num host de terceiro (PSP, provedor de jogo, SB) | reportar, chamado do lado deles |
| Erro de código novo | exceção que não existia; começou junto com um deploy | ver o diff do deploy → rollback vs. hotfix |
| Ruído conhecido | bate com o histórico do Slack ou com `memory/oncall/` | reportar e dormir |

Se nada encaixa, dizer que não encaixa em vez de forçar um balde.

## 2. Se a dúvida é "o pod caiu de verdade": ver no Freelens, não no Datadog

Quando o sinal é sobre tráfego/disponibilidade e existe a menor dúvida de que o próprio Datadog pode estar mentindo (métrica zerada, "No Data", etc.), nunca fechar o diagnóstico só com o Datadog. Confirmar por uma fonte que não passa por ele — Freelens (ou Lens/kubectl):

- **Lista de pods**: `Running`, `Ready`, contagem de restart. Vem da API do Kubernetes, não do Datadog.
- **Coluna de CPU/memória, na mesma lista**: vem do `metrics-server` do Kubernetes, também não é Datadog. CPU perto de zero em todos os pods ao mesmo tempo é sinal forte de que não tem carga real chegando — não é só métrica cega.
- **Aba de Logs do pod**: log real do container. Requisição sendo processada aparece aqui mesmo se o Datadog não estiver contando nada.
- **Se ainda em dúvida, exec no pod + `netstat`/`ss`**: confirma conexão TCP real, nível de sistema operacional. Mais invasivo, usar só se os anteriores não bastarem.
- **Pra saber se a requisição sequer chegou no cluster**: `RequestCount` do Load Balancer no CloudWatch (AWS) — fora do Kubernetes e fora do Datadog.

Regra prática: pod saudável (Running, sem restart) + CPU real ociosa = tráfego realmente não está chegando, o problema é externo ou upstream, não é problema de métrica. Pod saudável + CPU com atividade real + Datadog mostrando "No Data" = aí sim, suspeitar do próprio Datadog.

## 3. As 4 perguntas que decidem

Responder explicitamente, com evidência, antes de concluir qualquer coisa:

1. **Está crescendo?** Volume estável ou caindo quase nunca é emergência.
2. **Toca dinheiro ou jogador?** `payment` / `wallet` / `sb-wallet` sobem a régua. `statistics` / `segment` quase nunca.
3. **Recupera sozinho?** Tem retry, DLQ, cron que reprocessa?
4. **É reversível de manhã, ou o dado se perde?** Esta é a que de fato define acordar alguém.

## 4. Três saídas — sempre uma delas, nomeada

**CORRIGIR** — está ao alcance dele. Eu escrevo o passo a passo (comando do Rundeck, ajuste do ASG, query de verificação); ele executa; conferimos juntos e confirmamos que o sintoma parou. Não encerrar sem essa confirmação.

**ESCALAR** — fora do alcance dele. Destinatário: **VP – Janis**. Entrego o texto pronto: o que está quebrado, impacto, o que já foi verificado, o que precisa ser feito, e por que não pode esperar de manhã.

**REPORTAR E ESPERAR** — dá pra dormir. Texto do Slack + o que observar amanhã.

## 5. Report pro Slack

Cinco linhas, nada além:

```
[serviço] — o que está acontecendo (1 linha)
Impacto: quem/quanto está afetado, e se está crescendo
Causa provável: <balde> — <evidência que levou a isso>
Ação: <o que foi feito / o que vou fazer amanhã>
Aguarda dia útil: sim/não — por quê
```

## 6. Memória ao final

Escrever `memory/oncall/<AAAA-MM-DD>-<serviço>.md`: alerta, balde, causa raiz (ou "não confirmada"), ação, resultado. Se caiu em REPORTAR E ESPERAR, registrar o que checar depois.

A linha do índice em `MEMORY.md` aponta pra pasta `oncall/`, não pra cada incidente — a pasta cresce todo mês.

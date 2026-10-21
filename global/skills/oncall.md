---
description: Triagem de alerta de produção durante o oncall — classifica o alerta, decide entre corrigir agora, escalar ou reportar e esperar o dia útil, sem nunca escrever em produção.
argument-hint: <mensagem do PagerDuty/Slack ou erro do Datadog>
---

# oncall

Entrada para qualquer alerta de produção: mensagem do PagerDuty, erro do Datadog, ou "acordei com isso aqui". **Não é ticket** — não passa por `ticket-understand`, pelas fases do SDD nem por `ticket-code`.

A única pergunta que esta skill existe pra responder:

> **tem que agir agora, senão o sistema cai — ou dá pra reportar e resolver no próximo dia útil?**

Na prática quase nunca é bug de código. É spike de fila, job agendado travado ou dependência
externa. Investigar solto em produção às 3h da manhã custa mais do que resolve.

Canais de alerta, perfis de nuvem, escalonamento, quais serviços tocam dinheiro e o índice de
incidentes vêm do arquivo de referência de oncall do overlay (para a Celesta:
`celesta-microservices/oncall-reference.md`). Uma leitura só; se já foi lido no turno, não reler.

## Como a conversa roda

Vale o padrão de sempre (`../rules/writing.md`), com um agravante: é madrugada.

- Frases curtas, uma ideia por vez. Pergunta e resposta. A cabeça dele não pode cansar de ler antes
  de ele conseguir desligar.
- Zero relatório de IA. Sem preâmbulo, sem recap, sem repetir o que ele acabou de colar.
- Opinião real. Se o palpite dele sobre a causa não fecha com o que o log mostra, dizer na hora.
- **Antes de cada leitura, anunciar a intenção em uma frase**: "quero rodar essa query pra ver a carteira do usuário X", "quero olhar a profundidade da fila Y". Ele aprova ou corta.

## Guardrails de produção — inegociável

**Nenhuma escrita em produção pela minha mão.** Sem `UPDATE`/`DELETE`, sem rerun de job agendado,
sem alterar capacidade de auto scaling, sem restart, sem deploy, sem rollback.

Leitura é livre depois de anunciada:
- CLI do provedor de nuvem somente-leitura, com o perfil certo — atributos de fila, estatística de
  métrica, descrição de auto scaling, filtro de log
- `db-query` só `SELECT`
- Ferramentas de APM, de plantão e de chat quando autorizadas

Toda ação mutante vira **comando escrito para o usuário executar**, com o efeito esperado e como
reverter. Ele executa, não eu.

Se a ação corrige o sintoma sem explicar a causa (rodar de novo o job travado sem saber por que travou), dizer isso na hora — não deixar sair da conversa como se estivesse resolvido.

**Ambiente:** o canal de onde veio o alerta decide o perfil de nuvem — o mapeamento está na tabela
de contexto. Confirmar qual **antes** de qualquer leitura: olhar a fila do ambiente errado produz uma
conclusão errada com confiança total, que é o pior desfecho possível às 3h da manhã. Testar a sessão
com o comando de identidade do arquivo de referência antes da primeira leitura; expirada, pedir o MFA.

## 0. Histórico antes de investigar

Primeira coisa, sempre — antes de qualquer hipótese:

- Pedir para o usuário buscar nos canais de alerta pelo nome do monitor ou pela classe da exceção, e
  ler as threads. Ele esquece disso, e o debate antigo costuma já ter a resposta.
- Se a referência tiver canal de anúncio de mudança de infra, pedir para olhar as últimas mensagens
  dele. Uma mudança anunciada explica o alerta antes de qualquer hipótese de código.
- Casar o alerta com o índice de incidentes do arquivo de referência no mesmo momento. Abrir o
  arquivo do incidente só se uma linha casar.

Se já aconteceu: o que fizeram, funcionou, é o mesmo padrão? Se for, pular direto pro balde e ir pra decisão.

## 1. Triagem — cair num balde, não investigar solto

Perguntar o mínimo necessário pra escolher um dos cinco. O sinal que distingue vem primeiro; a ação, depois.

| Balde | Sinal que distingue | Ação típica |
|---|---|---|
| Spike / acúmulo de fila | profundidade da fila **subindo** vs. drenando; erro concentrado numa janela | drenando → observar; subindo → mais workers |
| Job agendado travado | horário bate com a janela do job; última execução pendurada, sem fim | matar e rodar de novo |
| Dependência externa | 5xx/timeout concentrado num host de terceiro | reportar, chamado do lado deles |
| Erro de código novo | exceção que não existia; começou junto com um deploy | ver o diff do deploy → rollback vs. hotfix |
| Ruído conhecido | bate com o histórico do canal ou com um incidente já registrado | reportar e dormir |

Se nada encaixa, dizer que não encaixa em vez de forçar um balde.

## 2. Se a dúvida é "o pod caiu de verdade": confirmar fora da ferramenta de APM

Quando o sinal é sobre tráfego ou disponibilidade e existe a menor dúvida de que o próprio APM pode
estar mentindo (métrica zerada, "No Data"), nunca fechar o diagnóstico só com ele. Confirmar por uma
fonte que não passa por ele — um cliente de Kubernetes como Freelens, Lens ou o próprio `kubectl`:

- **Lista de pods**: `Running`, `Ready`, contagem de restart. Vem da API do Kubernetes.
- **Coluna de CPU/memória, na mesma lista**: vem do `metrics-server` do Kubernetes. CPU perto de zero
  em todos os pods ao mesmo tempo é sinal forte de que não há carga real chegando — não é métrica cega.
- **Logs do pod**: log real do container. Requisição sendo processada aparece aqui mesmo que o APM
  não esteja contando nada.
- **Se ainda em dúvida, exec no pod + `netstat`/`ss`**: confirma conexão TCP real, nível de sistema operacional. Mais invasivo, usar só se os anteriores não bastarem.
- **Pra saber se a requisição sequer chegou no cluster**: a métrica de contagem de requisições do load
  balancer, no monitoramento do provedor de nuvem — fora do Kubernetes e fora da ferramenta de APM.

Regra prática: pod saudável (Running, sem restart) + CPU real ociosa = o tráfego realmente não está
chegando, o problema é externo ou upstream, não é problema de métrica. Pod saudável + CPU com
atividade real + APM mostrando "No Data" = aí sim, suspeitar da ferramenta.

## 3. As 4 perguntas que decidem

Responder explicitamente, com evidência, antes de concluir qualquer coisa:

1. **Está crescendo?** Volume estável ou caindo quase nunca é emergência.
2. **Toca dinheiro ou usuário final?** Serviço de pagamento ou de carteira sobe a régua; serviço de
   estatística ou de segmentação quase nunca. Quais são quais está na tabela de contexto.
3. **Recupera sozinho?** Tem retry, DLQ, cron que reprocessa?
4. **É reversível de manhã, ou o dado se perde?** Esta é a que de fato define acordar alguém.

## 4. Três saídas — sempre uma delas, nomeada

**CORRIGIR** — está ao alcance dele. Eu escrevo o passo a passo (o comando, o ajuste, a query de
verificação); ele executa; conferimos juntos e confirmamos que o sintoma parou. Não encerrar sem essa
confirmação.

**ESCALAR** — fora do alcance dele. Tier, destinatário e tempos estão no arquivo de referência.
Entrego o texto pronto: o que está quebrado, impacto, o que já foi verificado, o que precisa ser
feito, e por que não pode esperar de manhã.

**REPORTAR E ESPERAR** — dá pra dormir. Texto do Slack + o que observar amanhã.

## 5. Report para o canal

Cinco linhas, nada além:

```
[serviço] — o que está acontecendo (1 linha)
Impacto: quem/quanto está afetado, e se está crescendo
Causa provável: <balde> — <evidência que levou a isso>
Ação: <o que foi feito / o que vou fazer amanhã>
Aguarda dia útil: sim/não — por quê
```

## 6. Memória ao final

Escrever `<memória do projeto>/oncall/<AAAA-MM-DD>-<serviço>.md`: alerta, balde, causa raiz (ou "não confirmada"), ação, resultado. Se caiu em REPORTAR E ESPERAR, registrar o que checar depois.

Acrescentar uma linha no índice de incidentes do arquivo de referência (monitor, balde, saída,
arquivo). É ela que evita abrir arquivo no próximo alerta. A linha do `MEMORY.md` aponta para a
**pasta**, não para cada um — ela cresce todo mês.

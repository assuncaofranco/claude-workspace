---
name: oncall-2026-10-13-backoffice-logs-count
description: "prod-1 celesta-backoffice log_count 500, activity /user-activities/aggregate demorando ~20s; issue de 2 meses, reportar e esperar"
metadata:
  node_type: memory
  type: project
  originSessionId: 9ae3c54a-e4cf-43f8-a2ed-299e2136b861
  modified: 2026-10-13T10:28:19.438Z
---

**Alerta:** Datadog Error Tracking, monitor de issue novo, P3. `celesta-backoffice` `log_count` (`POST /api/gateway/logs/count`) com `GuzzleHttp ClientException 500` vindo de `http://activity-active/api/user-activities/aggregate`. 2026-10-13 11:03 UTC+1, prod-1.

**Balde:** ruído conhecido / lentidão de dependência interna. O span levou 20,1 s antes do 500, então o `aggregate` do activity estourou o tempo. Disparado por um usuário do BO abrindo uma tela de logs. O issue existe desde a v1.1331 (~2 meses) e voltou na v1.1420; não está ligado a deploy recente.

**Causa confirmada pelo erro do activity:** `userActivityRepository.GetUserActivitiesAggregate` → `runReadCursor` no DocumentDB `celesta-prod-1-documentdb` dá `context deadline exceeded ... i/o timeout`. A contagem é lenta no banco; o BO só repassa o 500. Para o ticket de amanhã: índice ou limite de janela na agregação de count, e ver no CloudWatch a CPU/latência do DocumentDB nesse horário.

**Recorrente:** mesmo `issue.id` já disparou no PagerDuty em 2026-10-06 14:43 (resolvido) e há 4 ocorrências na busca do canal. Ler as threads antigas antes de investigar de novo.

**Sem relação com o CLS-1546**, que o Lucas perguntou: os PRs ainda estavam abertos, e o ticket não mexe no activity nem no `logs/count`.

**Saída:** REPORTAR E ESPERAR. Sem impacto em dinheiro ou jogador; o usuário pode tentar de novo.

**Para amanhã:** ver se vale ticket para a query de contagem do activity (índices no Mongo, ou limite de janela/filtro obrigatório no count). Não verificado: a frequência no Datadog e o filtro que o usuário usou.

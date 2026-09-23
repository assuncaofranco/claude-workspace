---
name: project-cel8734-drift-schedule-check
description: Perguntar ao Lucas se o drift agendado do lrgi-terraform rodou — pendente desde 2026-09-17
metadata: 
  node_type: memory
  type: project
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-16T10:45:05.300Z
---

**Perguntar ao Lucas, a partir de 2026-09-17:** o drift agendado do
`lrgi-terraform` rodou?

```
gh run list --workflow drift.yml --repo celesta-tech/lrgi-terraform
```

Um run que ele não disparou = funcionou. Só isso fecha o assunto.

**Pré-condição:** o cron só existe depois que o PR #50 (CEL-8734) entrar na
master — GitHub só agenda workflow que está na branch default. Em 2026-09-16 o
PR estava aberto e não mergeado. Se ainda não mergeou, a pergunta rola para o
dia seguinte ao merge, não some.

`cron: '10 7 * * 1-5'`, UTC, dias úteis.

**Por que isso não é preciosismo:** se o cron não disparar, nada acontece — sem
erro, sem run vermelho, sem alerta. Um detector de drift que nunca roda parece
idêntico a um que roda e não acha nada, e o resultado é confiança falsa. O resto
do workflow já está provado em 5 runs; o cron é a única parte que não dá para
testar, só verificar.

**Risco recorrente, ainda em aberto:** o GitHub suspende workflows agendados
depois de 60 dias sem commit no repo, e o `lrgi-terraform` era quieto antes deste
épico. Ou seja, o drift pode parar sozinho e em silêncio por volta de
**2026-11-15**. Duas saídas levantadas, nenhuma decidida, e é pergunta para o TL:
aceitar (é o que o `celesta-casino-terraform` faz hoje) ou mandar um batimento
semanal às segundas mesmo quando está limpo, para a ausência da mensagem virar o
sinal.

Contexto do épico em [[project-cel8469-lrgi-terraform-audit]].

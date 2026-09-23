---
name: cls1872-cls2980-gateway-endpoint
description: "CLS-1872/CLS-2980 — o time criou um endpoint novo no celesta-gateway mas já existia um antigo: decisão é usar o antigo e alinhar com o front"
metadata: 
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-21T07:19:08.278Z
---

Daily de 2026-09-21: o time informou que criou um **endpoint novo no `celesta-gateway`** para o
fluxo de game connections, mas que **um endpoint antigo equivalente já existia**.

**Decisão: usar o antigo.** O novo não deve ser adotado. Alinhar com o **time de front** antes de
implementar qualquer coisa que dependa disso.

**Why:** duplicar rota no gateway para o mesmo recurso cria dois contratos para o front manter e
duas superfícies de permissão para auditar — exatamente o tipo de dívida que o épico CLS-1872 está
tentando reduzir ao centralizar a gestão de game gateways no Backoffice.

**How to apply:** ainda **não** foi verificado em código qual é o antigo e qual é o novo — isso é
uma informação de daily, não um achado de repositório. Identificar os dois endpoints só quando o
trabalho chegar na parte de gateway/front, e confirmar com o time de front qual deles eles já
consomem. Não assumir nenhum dos dois antes disso.

Contexto técnico completo do ticket em [[cls1872-cls2980-findings]].

---
name: project-change-cards-pilot
description: "Piloto combinado em 2026-10-12 — cards de mudança preenchidos pelo Lucas, conferidos por mim, para ele reter o domínio dos tickets; rodar no próximo ticket"
metadata:
  node_type: memory
  type: project
  originSessionId: b9fa30c9-8ca4-4da8-b4d6-6ba47016cb41
  modified: 2026-10-12T08:09:42.095Z
---

Combinado em 2026-10-12, ainda não é regra (não passou por `corpus.md`): no próximo ticket que chegar,
pilotar os "cards de mudança".

**Por quê:** o Lucas sente que o domínio dos tickets não fica na cabeça desde que trabalha comigo; o
`explain` não resolve porque ele só lê. O objetivo é retenção, não documentação.

**Como aplicar:**
- Depois de entender o ticket e **antes** do código; as respostas viram a spec, cada "depende de X"
  vira linha da matriz.
- Eu conduzo uma cascata de perguntas (múltipla escolha quando fechada): tipo (HTTP, entidade, job…),
  ação (criar, alterar, apagar), MS, depois URL/payload/response/tipos, entidade (nullable etc.),
  listener, mensagem, condições, consumers.
- **Ele responde, eu confiro com o código** e aponto só o erro, com arquivo e linha. Em modificação,
  ele chuta o estado atual antes de eu mostrar.
- Marcar delta (`+ ~ −`), não o estado inteiro.
- Começar com três modelos (HTTP, entidade, job), ajustar no uso; os modelos vão para
  `claude-workspace/templates/`, a saída para `changes.md` na pasta do ticket.
- Software (wizard) só depois que os modelos estabilizarem.

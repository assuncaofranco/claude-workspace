---
name: game-nginx-body-capture
description: "O sidecar nginx de celesta-game e promotion captura request/response body inteiro no access log — confirmado em prod com credencial em texto claro. Detalhe técnico completo em ~/.claude-secrets/celesta-prod-findings.md, fora do git."
metadata:
  node_type: memory
  type: project
  originSessionId: ac86a1f1-7cb7-43de-b034-de3b1dcd6c74
  modified: 2026-09-22T00:00:00.000Z
---

O sidecar nginx do **celesta-game** e do **promotion** grava body de request e resposta no access
log, com dois destinos (Datadog e S3). Confirmado em produção em 2026-09-22: credencial de carteira
em texto claro no log indexado. O vazamento existe hoje, independente do CLS-1872.

**O conteúdo completo não está neste arquivo.** Ele vive em
`~/.claude-secrets/celesta-prod-findings.md`, fora da árvore do git — e fica lá enquanto a falha
estiver aberta.

O motivo não é pudor: o documento junta, num texto só, a rota sem autenticação, a ausência de
expiração do token, o hash do segredo não rotacionado e a query exata que encontra a credencial nos
logs. Isso é um roteiro de exploração contra a carteira do jogador. Um repositório — mesmo privado,
mesmo numa conta pessoal — é o lugar errado para ele.

**O que fica aqui, porque é o que o trabalho do dia a dia precisa saber:**

- **Bloqueia o deploy do CLS-2978/2979.** Os dois põem credencial de provedor no corpo de uma
  resposta e de uma requisição que passam pelo nginx logado. Não deployar antes de resolver a
  captura. Dono: DevOps, com provável envolvimento de segurança/DPO pelo dado pessoal.
- **Testar em preprod com credencial real de provedor escreve essa credencial nos logs de preprod.**
  A captura está na base do kustomize, sem overlay que a desligue — vale para os seis ambientes.
- **Mitigação acionável no CLS-2981:** enviar `options` só quando o editor foi de fato modificado.
- **Ordem das ações é contraintuitiva:** parar a captura primeiro (unilateral, rápido), rotacionar
  depois. Rotacionar antes quebra a integração e ainda loga o token novo.
- **O backoffice loga só a linha de requisição**, sem body nem header. A exposição do CLS-1872 é um
  salto só: backoffice chamando game.

**Why:** é ticket próprio e prioritário, não um detalhe do épico.
**How to apply:** ver o arquivo no vault antes de qualquer conversa sobre deploy do CLS-1872.
Relacionado: [[cls1872-review-2026-09-22]], [[feedback_never_fix_outside_ticket_scope]].

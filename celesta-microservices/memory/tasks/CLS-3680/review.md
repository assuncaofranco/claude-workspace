---
name: cls-3680-review-document-created-doc
description: "Review 2026-11-10 do CLS-3680 (notification #173, Socrates) — doc do document-created no AsyncAPI depois do re-split do CLS-43; código ok, só nits opcionais"
metadata:
  node_type: memory
  type: project
  originSessionId: 127f4e64-c6c1-4e77-91da-b89251131298
  modified: 2026-11-10T08:03:12.676Z
---

# CLS-3680 — review da doc do `document-created` (notification PR #173)

Sub-task do CLS-43 (notificar brand quando BO cria slot de documento). Autor Socrates. Revisado em
2026-11-10, ticket em To review.

**Re-split 2026-11-06 (Marco):** `document-created` virou *mensagem* no tópico `{ID}-document`
existente, não tópico novo. Por isso o proteus #738 (que listava `document-created-channel` no
pcn-1) foi declinado, o CLS-4570 foi apagado e o CLS-3681 (terraform) virou revert do SSD-747.

**Conferido contra a realidade, não só o diff:**
- crm #2147 (`DocumentController::dispatchDocumentCreatedNotification`) manda exatamente
  playerId/documentId/documentType/status/timestamp(`microtime(true)`), mesmos nomes e tipos do
  `status-updated` em `DocumentSubscriber`. Bate com o schema.
- Go do notification não valida `EventType` nem `Topic` (`sender.go`, helper `message.Notification`):
  o header `type` é repassado. "Sem mudança de Go" é verdade. `document` é provisionado pelo
  `Setup()`.
- pcn-1 do Proteus assere canais, não mensagens; CI do proteus verde no 4ddb11bb.

**Nits opcionais (não postados, mostrados ao Lucas):** operation `{ID}-document` ainda diz
"Document updated messages"; enum do schema base `Notification` não tem `document-created` (já
faltavam outros tipos, drift antigo); título do PR ainda fala em "topic".

**Desfecho:** aprovar. Review anterior do Lucas (03/11) ficou DISMISSED pelos commits novos.

**Why:** registrar que o doc-vs-crm foi cruzado, para não refazer se o ticket voltar.
**How to apply:** se o crm #2147 mudar o payload antes do merge, reconferir o schema aqui.

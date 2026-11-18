---
name: reference-celly-dev-login
description: "Login do Celly Dev (localhost:8080): usuário lfranco; se o Lucas esquecer a senha, responder só com a pergunta-lembrete dele"
metadata:
  node_type: memory
  type: reference
  originSessionId: 3e7939c6-8d24-4708-9d89-b2aaa51ac270
  modified: 2026-11-09T14:08:48.621Z
---

Login do Celly Dev ([[project-personal-app]]): usuário **`lfranco`**. A senha é a mesma do e2e e está
no 1Password, cofre Employee, item `claude-celesta-e2e`.

Token do Jira do Celly Dev: item `claude-jira` (cofre Employee, campo `credential`), token com
scopes chamado `celly-dev`, criado em 2026-11-09, **expira em 2027-11-10** (o máximo que a Atlassian
permite, 366 dias). Scopes só de leitura, os seis: `read:jira-work`, `read:jira-user`,
`read:board-scope:jira-software`, `read:board-scope.admin:jira-software`, `read:project:jira`
(configuração do board) e `read:jql:jira` (quick filter). Os dois últimos faltaram no primeiro token
e a API de Agile respondeu 401 `FAILURE_CLIENT_SCOPE_CHECK`; a fonte dos scopes por rota é o
`swagger.v3.json` da Atlassian (campo `security`), não a página de docs, que vem cortada. Token com
scope só funciona por `api.atlassian.com/ex/jira/<cloudId>`. Quando o board começar a responder 401
perto da expiração, é o token: criar outro igual em id.atlassian.com e trocar no item.

Quando o Lucas esquecer a senha, dizer a pergunta-lembrete que ele escolheu: **"qual o filho do ano?"**.
Nunca a senha em si, nem tentar adivinhá-la ou lê-la do 1Password para mostrar no chat.

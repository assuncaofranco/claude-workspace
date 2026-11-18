---
name: project-personal-app
description: "App pessoal Lucas+Claude = Celly Dev, `celly-dev/` (cópia podada do celesta-e2e-tests, roda no host); board rodando com Jira real desde 2026-11-09; catálogo de requests (Requests) feito, falta testar contra local/PP1; próximo é o chat"
metadata:
  node_type: memory
  type: project
  originSessionId: ff9e9d9c-f77c-40b1-82ba-76456a63c145
  modified: 2026-11-13T11:40:18.294Z
---

App que junta o dia a dia: tickets no SDD, chat por ticket e chat "colega", ambientes, oncall.
Plano e lista de 14 itens em `~/.claude/plans/vamos-criar-nossa-propria-prancy-sundae.md`.

Decidido em 2026-11-04 (revê 11-02):
- **Base = cópia do `celesta-e2e-tests`** em `celesta-projects/celly-dev/` (nome Celly Dev, renomeado de cockpit em 2026-11-04), repo na **conta pessoal
  do Lucas** (ele assume: o e2e é ferramenta do Rasoul, não produto). O e2e original nunca é editado.
  Isso substitui o "sem fork, conversar por MCP" de 11-02.
- **Roda no host, sem Docker**, preso em 127.0.0.1, CORS com allowlist local: o app age como o
  usuário (`claude`, `gh`, `kubectl`, `aws`). Go instalado via brew em 2026-11-04 para isso.
- **Chat dentro do app**, com o Claude Code por baixo.
- **Tudo em inglês** (2026-11-09): tela, textos de estado SDD, avisos e o objetivo gerado,
  porque o Lucas pode precisar mostrar o app. Conversa com ele continua em pt.
- **Ordem:** 0 cópia e poda (feito, 3 commits locais) → 1 board + estado SDD por regra → 2 chat por
  ticket + botão → 3 resto (inbox, preprod, k8s, oncall/AWS MFA, pré-push, terceiros, stack).

Estado em 2026-11-04: o runner de teste saiu, o helper Python do e2e virou `internal/jira` +
`internal/github` (via `gh`), e o Deployments/Jenkins foi herdado. Remote: `origin` = `assuncaofranco/celly-dev`
(privado; HTTPS com o usuário na URL, porque o `gh` está logado como `lucasfranco83`, que não
enxerga o repo), `upstream` = e2e com push `DISABLED`. Jira via token com scopes no item `claude-jira` (ver [[reference-celly-dev-login]]); Jenkins via item "Lucas Franco Jenkins".

Board (passo 1, 2026-11-04): desenho do Lucas = kanban por status do pai (colunas do board 387),
card do pai expande as sub-tasks, filtro por dev (ele, Rasoul, Bohdan, Socrates, Marcello TL), spec/split
no pai e plan/implement/review na sub-task (botões desligados até o passo 2). Pais = filtro do board 387
+ quick filter 873, lidos ao vivo (o board 589 é o das sub-tasks). Reverificação no GitHub só quando o
card expande. Fluxo Jira: pai Backlog→Ready→Split→Implementing→Preprod ready→In preprod→In prod;
sub-task To Do→Planned→In Progress→To review→**Implemented (= review aprovado)**→Testing→Done
(conferido no changelog em 2026-11-10; eu tinha suposto Implemented antes de To review, e o board
mandava revisar o que já estava revisado). To review é espera na sub-task do Lucas e ação na do colega. O label sdd-spec quase nunca
é posto, então o status manda. `claude` não está no PATH: o app usa o binário da extensão do VS Code.

Dados reais do board (2026-11-09): board 387 = filtro 12158 (`project in (Celesta)`, sem sub-tasks)
+ quick filter 873 `component in (D-Team)`; colunas Backlog, READY, Split, DEVELOPING, PREPROD READY,
IN PREPROD, PROD READY, IN PROD. ~160 pais (89 em Backlog), ~330 sub-tasks. Épicos entram no filtro
mas ficam fora das colunas, então o app descarta pai sem coluna, como o Jira faz. O objetivo do card
(`claude -p`) só é gerado ao expandir, senão seriam ~160 chamadas por load.

Achado para o passo 1: PR de hotfix sem a chave no título nem na branch (promotion #554,
`hotfix-schedule-occurrence`, CLS-3734) não aparece por busca de chave.

**Why:** Lucas quer um assistente que o mantenha atento, e eu posso pedir coisas que me facilitem.
Ferramenta mais genérica (2026-11-12, `d5fd77b`): além da visão do D-Team, entra todo pai do CLS
atribuído ao Lucas ou com sub-task dele, em qualquer time ou sprint (`BOARD_MINE_PROJECT`, só CLS
por decisão dele). Seletor Both / Mine / D-Team, card com componente e sprint (campo
`customfield_10020`, achado pelo schema), status sem coluna vai para "Other". Épico sai pelo nível de
hierarquia: o CLS tem "Technical Epic", que um `issuetype != Epic` não pega.

Hook de permissão (2026-11-12, `bd207c6`), instalado em `~/.claude/settings.json` como
`PermissionRequest`: `backend/bin/celly-hook` decide por regra fixa (`internal/permit`, parser de shell
`mvdan.cc/sh`), só libera ou cala, nunca nega; tudo vai para `permission_log` e para a página
Permissions. Motivo: 1140 regras de allow e ainda pedia o básico. Depois de mexer nas regras, `make hook`
(pede confirmação, de propósito: o binário é protegido). Ler o log pelo `sqlite3` pede autorização,
porque `celly-dev/data` é protegido; usar a página. Parte 2 (aprovar o resto longe da mesa) ainda não
feita: o settings tem `inputNeededNotifEnabled` (push no celular quando um pedido espera) e Remote
Control; testar isso antes de construir algo.

Fluxo no painel (2026-11-12, `fb96511` deploy, `6e98157` chat/fluxo). Lista final de 19 etapas
aprovada pelo Lucas (nosso fluxo e o do SDD intercalados; gate 1 no rascunho do plano, gate 2 no
push), em `internal/flow`. Desenho dele: em cada ticket, botão da etapa atual (um por opção) +
**Complete**, que roda até um agente pedir resposta; chat lateral substitui o VS Code, sem ligação
com ele. Sessões headless por ticket × papel (coordenação/execução, da ticket-story) + geral;
marcador `[[step:done|waiting]]` no fim de cada turno. Deploy em preprod pelo Jenkins na página do
ticket, por grupo do manifesto, só com review APPROVED + CI verde + grupo anterior verde; Complete
sempre para antes. Hook com timeout 900 no settings: sessões do painel esperam o Allow/Deny no chat.
Armadilha: `make hook | head -1` não troca o binário: o `head` fecha o pipe, o make morre de
SIGPIPE antes do `go build` terminar (visto 3 vezes, causa achada em 2026-11-13). Nunca encadear
`make` com `head`; conferir com `bin/celly-hook --version` (commit embutido desde `4c100a7`).
Reiniciar o servidor mata as sessões do painel que estão vivas: em 2026-11-13 11:15 eu matei a
execução do CLS-1214 no meio de um Bash. Antes de `make up` de novo, ver `pgrep -P <pid do :8080>`
e se algum transcript foi escrito no último minuto.
Ainda não exercitado: a UI logada, um Complete com skills de verdade, o primeiro deploy real.

Limpeza das permissões (2026-11-12, decisão do Lucas): `~/.claude/settings.json` allow 1170 → 54
regras genéricas (leitura, git/gh/make/go/docker/npm run, Edit dentro dos projetos, memória e /tmp) e
ask 25 → 43 (PR comment/create/review, docker rm, .env, CLAUDE.md, claude-workspace/global, bin e data
do celly-dev). Fora do allow de propósito: python3, php, node, bash -c, xargs, find, sed, awk, curl,
rm, que o hook julga. python3 e php: o Lucas quer um agente autorizando com regras próprias, depois.
`settings.local.json` do celesta-projects 191 → 0;
as 25 de ask ficam. Motivo: 113 regras com texto de credencial e 4 amplas que passavam por cima do
hook. Backups `*.bak-2026-11-12` (chmod 600, contêm credencial: apagar depois de uns dias). O que
voltar a perguntar vira regra no hook, com teste, nunca regra no settings. Próximo combinado: scripts
nossos com variáveis numa pasta protegida (claude-workspace/bin), que o hook libera; aí sai o
python3/php.

**How to apply:** passo 1 (board) fechado em 2026-11-10, tudo no GitHub.
Ao retomar, o próximo é o passo 2 (chat): sessão do Claude Code por ticket, aberta pelo botão do card
com a skill da fase e o resultado da verificação; tabela ticket → session id; painel lateral no board.
Pergunta aberta, sem resposta ainda: o que a sessão faz sem perguntar (minha proposta: cada
permissão vira Allow/Deny no painel). Pendências menores: Requests nunca rodou contra local/PP1
(falta domainId e usernames em `catalog/environments.json`); as cores novas não foram conferidas
na tela por mim. Não reabrir cópia × MCP nem host × Docker.

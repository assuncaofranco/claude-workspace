---
name: project-permission-judge
description: "Como as permissões dos chats são decididas (regras fixas, juiz de modelo, settings.json), por que o juiz foi ligado nos chats normais em 2026-11-18, o que nunca vai para ele e como auditar"
metadata:
  node_type: memory
  type: project
  originSessionId: 9d434eac-aa16-47ab-af8b-e3bbc4988b28
  modified: 2026-11-18T07:45:03.756Z
---

**Meta do Lucas (2026-11-18):** permissão não pode parar a produtividade. Só para quando sai da máquina
local, quando há dúvida, ou quando a decisão depende dele.

## Camadas, na ordem em que um pedido passa

1. `settings.json`: `allow` e `ask` do Claude Code. Um `allow` que casa resolve sozinho: não abre
   diálogo, não chama o hook, não gasta token de juiz.
2. Hook `PermissionRequest` = `celly-hook` (`celly-dev/backend/cmd/hook`), só roda quando o diálogo ia abrir.
   - Regras fixas (`internal/permit`, sem modelo, grátis): leitura, escrita nas raízes do projeto, bash
     que o parser (`mvdan.cc/sh`) reconhece como seguro. Só diz "allow" ou nada.
   - **Juiz de modelo** (`internal/judge`, `claude -p --tools ""` com sonnet, ~6s): só Bash que as regras
     fixas deixaram aberto. Antes dele, a lista `outward` (push, gh de escrita, curl com corpo, kubectl que
     muda, aws que muda, ssh, docker push, Jenkins) vai direto ao Lucas sem modelo.
3. Sessão rodada pelo painel Celly (`CELLY_RUN`): o que sobra vai ao painel (Allow/Deny no chat) e o
   juiz de lá só atende a coordenação.

## O que mudou em 2026-11-18

Antes o juiz de modelo só existia no painel. Nos chats do VS Code o hook tinha só as regras fixas, e
~1.500 pedidos em 7 dias abriram diálogo, quase todos locais: `python3` heredoc (430), `perl` (70),
path montado em runtime `S=/tmp/...` (~110), `docker compose` com helper (95), `git symbolic-ref`.
Agora, fora do painel, o hook chama o juiz para Bash aberto (`judgeOpen`, orçamento 30s; erro, dúvida
ou timeout = diálogo como antes). Código em `cmd/hook/main.go`, binário `backend/bin/celly-hook`,
backup do anterior `celly-hook.bak-2026-11-18` na mesma pasta.

## Nunca vai ao juiz (continua com o Lucas)

Credencial (`.env`, `.claude-secrets`, `.ssh`...), caminho protegido (`settings`, hooks, `global/`,
`CLAUDE.md`, `.git/`, `celly-dev/data|bin`), qualquer MCP de escrita (Jira, Slack), Edit/Write fora das
raízes. **Por quê:** o allow do hook passa por cima das regras `ask` do `settings.json`; o juiz não
conhece essas regras, então elas não podem depender dele.

## Auditar

`permission_log` em `celly-dev/data/celly-dev.db`. `rule` começa com `judge allowed: <motivo>` quando o
juiz liberou e termina em `| judge asked: <motivo>` quando mandou ao Lucas.

```
sqlite3 -readonly data/celly-dev.db "select allowed, substr(rule,1,90), count(*) from permission_log where at > datetime('now','-1 day') group by 1,2 order by 3 desc"
```

## Tokens: as regras do settings.json não são o custo

As ~219 entradas de `allow` não vão ao contexto do modelo, então não gastam token. Apagá-las **aumenta**
o gasto: o que elas resolvem passaria a chamar o juiz (uma chamada de sonnet + ~6s cada). O custo real é
só o número de chamadas do juiz. 42 entradas são one-off mortas (path de sessão `/private/tmp/claude-502/...`,
`perl -pi` de um arquivo, `awk 'NR>=95'`): nunca casam de novo, só poluem; podar é seguro mas não poupa token.

## Pendente / limites conhecidos

- O juiz só lê o comando, não o conteúdo de um script chamado por caminho (`python3 -I /tmp/x.py`):
  o prompt manda liberar script local, então confia no caminho.
- `Monitor` (10 paradas/semana) não passa pelo juiz.
- Sem teste automatizado de `judgeable`/`judgeOpen`; testado à mão com 6 pedidos.
- Hook `UserPromptSubmit` aponta para `~/.claude/hooks/inject-project-instructions.sh`, que não existe.
- Primeira medição real (quantos `judge allowed` por dia e o custo) ainda por fazer.

Relacionado: [[project-personal-app]] (Celly Dev), [[project-our-services]].

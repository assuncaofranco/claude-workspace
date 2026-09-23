---
name: claude-workspace-repo
description: "Desde 2026-09-23, skills/memória/padrões moram no repositório claude-workspace e ~/.claude aponta para lá por symlink; credenciais vivem em ~/.claude-secrets, fora do git"
metadata:
  type: project
---

Skills, memória, padrões e hooks são versionados em
`~/Desktop/celesta-projects/claude-workspace/`, remoto na conta pessoal `assuncaofranco` (não a
`lucasfranco83` que assina os repositórios da `celesta-tech` — são duas contas, e a identidade é
travada **por repositório** porque o workspace fica dentro da pasta dos repos da empresa).

`~/.claude/` aponta para lá por **symlink de diretório**: `commands`, `memory`, `shared`, `hooks`,
`postman` e os dois `projects/<slug>/memory`. `~/.claude/CLAUDE.md` é a exceção — stub com `@import`,
porque symlink de *arquivo* quebra quando um editor escreve num temporário e renomeia por cima.
`settings.json` também fica real: o Claude Code o reescreve a cada permissão aprovada; `make snapshot`
copia para o repositório removendo credenciais.

**Divisão por dono, não por tipo de arquivo:** `global/` é o método e não menciona empresa nenhuma;
`celesta-microservices/` e `celesta-infra/` são o contexto. Apagar os dois últimos não tira nada do
primeiro — `make portable` testa isso resolvendo cada link e `@import` de `global/` com o resto
apagado.

**Nenhuma credencial no repositório.** Elas vivem em `~/.claude-secrets/` (chmod 700), **fora da
árvore do git** e não numa pasta ignorada: `git add -f`, clone com `.gitignore` antigo ou merge mal
resolvido furam pasta ignorada, e do histórico um segredo só sai reescrevendo o histórico. As skills
referenciam o caminho, nunca o valor.

**Why:** o conhecimento vivia solto em `~/.claude`, sem git, sem histórico e sem backup, misturando
três coisas de donos diferentes. E a extração revelou que `preprod-test.md` e `ticket-postman.md`
carregavam credencial viva protegida só por `chmod 600` — que não sobrevive a um `git push`.

**How to apply:** editar os arquivos onde eles estão (pelo symlink ou direto no repositório, dá no
mesmo) e commitar no workspace. Antes de push: `make secrets-scan`, `make portable`, e o grep de
atribuição de IA. Em máquina nova, `./bootstrap.sh` — mas ele **não** recria `~/.claude-secrets/`,
que por definição nunca esteve no repositório. Onde cada specific da Celesta foi parar:
`context.yaml`, `db-reference.md`, `postman-reference.md`, `constants-backlog.md`.

Relacionado: [[preferences]], [[feedback_local_postman_collections_folder]],
[[feedback_epic_planning_folder]].

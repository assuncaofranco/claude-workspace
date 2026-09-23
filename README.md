# claude-workspace

Método de trabalho, skills e memória — versionados, para não morrerem num diretório de configuração
sem histórico e sem backup.

O repositório é dividido por **dono**, não por tipo de arquivo. Essa é a única regra de organização
que importa aqui:

```
global/                  o método. É meu, vai comigo, não menciona empresa nenhuma.
celesta-microservices/   contexto da Celesta — serviços, memória de ticket, incidentes.
celesta-infra/           contexto da infraestrutura.
```

Apagar `celesta-*` não tira nada de `global/`. É a promessa do repositório, e `make portable` a testa.

---

## Como isto se liga ao Claude Code

O Claude Code lê de `~/.claude/`. Os arquivos moram aqui e `~/.claude/` aponta para cá por **symlink
de diretório**:

| `~/.claude/…` | aponta para |
|---|---|
| `commands/` | `global/skills/` |
| `memory/` | `global/memory/` |
| `shared/` | `celesta-microservices/shared/` |
| `hooks/` | `celesta-microservices/hooks/` |
| `postman/` | `celesta-microservices/postman/` |
| `projects/<celesta>/memory/` | `celesta-microservices/memory/` |
| `projects/<infra>/memory/` | `celesta-infra/memory/` |

`~/.claude/CLAUDE.md` é a exceção: fica arquivo real, um stub com três `@import` para cá. Symlink de
**arquivo** quebra quando um editor escreve num temporário e renomeia por cima; symlink de
**diretório** não tem esse problema. Daí o corte.

```bash
./bootstrap.sh          # monta ou repara tudo — idempotente
./bootstrap.sh --check  # só verifica, não escreve
```

---

## Segredo nenhum aqui

Credenciais vivem em `~/.claude-secrets/`, **fora da árvore do git**. Não numa pasta ignorada: fora.

Uma pasta ignorada ainda vaza por `git add -f`, por clone com `.gitignore` antigo, por rename, por
merge mal resolvido. Fora do repositório nenhum desses erros alcança o conteúdo. As skills referenciam
o caminho, nunca o valor.

Duas redes a mais, porque a primeira pode falhar:

- `.githooks/pre-commit` barra o commit quando acha padrão de segredo no conteúdo *staged*
- `make secrets-scan` varre o working tree **e todo o histórico** — porque do histórico um segredo só
  sai reescrevendo o histórico

Coleção de Postman versionada carrega o **nome** da variável com valor vazio; o valor entra na
environment do runner em tempo de execução.

---

## Comandos

```bash
make bootstrap      # monta/repara os symlinks
make check          # verifica sem escrever
make snapshot       # copia o settings.json vivo, removendo credenciais da allowlist
make secrets-scan   # procura segredo no working tree e no histórico
make portable       # global/ sobrevive sem celesta-*? é a promessa do repositório
```

E os que economizam contexto no dia a dia, lendo `celesta-microservices/context.yaml` para saber
container, alvo de make e porta de cada serviço:

```bash
celesta-microservices/scripts/install.sh <serviço>   # make init + build + openapi
celesta-microservices/scripts/test.sh <serviço>      # make test + o fim do phpunit.log
celesta-microservices/scripts/lint.sh <serviço>      # phpinsights
celesta-microservices/scripts/openapi.sh <serviço>   # regenera a doc
```

Aceitam o nome completo, um sufixo (`wallet`), ou nada quando você já está dentro do repositório do
serviço.

---

## Markdown ou YAML

Híbrido, e a divisão é deliberada:

- **Markdown para prosa** — skills, CLAUDE.md, memória, decisões. É o que o modelo lê nativamente e
  custa menos contexto que JSON aninhado dizendo a mesma coisa.
- **YAML para tabela de consulta** — `context.yaml`: serviços, alvos de make, prefixos de commit,
  mapa de domínio, portas. Um arquivo que o modelo e os scripts leem, então o dado existe uma vez só.

---

## Numa máquina nova

```bash
git clone <url> ~/Desktop/celesta-projects/claude-workspace
cd ~/Desktop/celesta-projects/claude-workspace
./bootstrap.sh
```

O `bootstrap.sh` cria os symlinks, escreve o stub, instala o hook e confere a identidade do git.
O que ele **não** pode fazer é recriar `~/.claude-secrets/` — esse diretório nunca esteve aqui,
por definição. Copie-o à mão, de um gerenciador de senhas ou de um disco cifrado.

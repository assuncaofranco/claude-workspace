# Celesta — overlay

O que é específico da Celesta. O método genérico está em [`../global/CLAUDE.md`](../global/CLAUDE.md);
as tabelas de consulta em [`context.yaml`](context.yaml). Este arquivo não repete nenhum dos dois.

Arquitetura de microserviços. A lista de serviços, alvos de `make`, containers, portas, mapa de
domínio e prefixos de commit estão todos no `context.yaml` — é ele que os scripts leem.

Contexto compartilhado: [arquitetura](shared/architecture-patterns.md) ·
[padrões de código](shared/coding-standards.md) · [estratégia de teste](shared/testing-strategy.md) ·
[referência de Postman](postman-reference.md) · [Datadog: logs × traces, prod-2](datadog-reference.md)

---

## OBRIGATÓRIO — antes de qualquer ação num serviço Celesta

Antes de rodar comando, escrever código ou responder pergunta sobre um serviço:

1. Se a mensagem menciona ou implica um ticket, rodar `ticket-understand` **primeiro**.
   **Exceção:** alerta de produção não é ticket — ver abaixo.
2. Identificar o serviço envolvido (pelo diretório ou pelo pedido)
3. Reler as regras de código deste arquivo antes de escrever PHP ou criar commit

Vale para tudo: rodar testes, corrigir bug, adicionar feature, responder pergunta sobre o código.

---

## Alerta de produção — oncall

Alerta de produção — PagerDuty, erro do Datadog colado, qualquer coisa vinda dos canais de alarme, ou
menção a estar de oncall — vai para `/oncall`, **não** para o fluxo de ticket. Sem
`ticket-understand`, sem `sdd-*`, sem código. É produção: investigação somente-leitura, e toda
ação que muda estado é escrita para o Lucas executar ele mesmo.

Entrar ou sair do turno, sem alerta, é `/oncall-shift`. Canais, perfis, escalonamento, checklist e
índice de incidentes: [`oncall-reference.md`](oncall-reference.md).

---

## Rodando testes

Nunca rodar teste direto no host. Os Makefiles já encapsulam o docker:

```bash
make test        # phpunit; resultado em var/log/phpunit.log
make lint        # phpinsights
make openapi     # regenera public/open-api.json (não é versionado)
make init        # sobe a stack e roda install.sh
```

Ou os scripts que empacotam a sequência: `scripts/install.sh <serviço>`, `scripts/test.sh <serviço>`.
Quais alvos existem em qual serviço está em `context.yaml` — nem todo serviço tem todos.

**Depois de troca grande de branch, rodar `make init` antes de confiar em resultado de teste.** Cache
de Doctrine e banco de teste velhos produzem erro que parece regressão e não é.

---

## Bibliotecas compartilhadas

Certo código **não pode** nascer dentro de um serviço:

| O quê | Biblioteca | Regra |
|---|---|---|
| Constantes | `celesta-constants` | Nunca criar constante dentro de um serviço |
| Jobs de messenger | `celesta-job-library` | Nunca criar classe de job dentro de um serviço |

Quando a tarefa exige constante ou job novo, **parar e avisar** que precisa ser criado na biblioteca
primeiro. Para mudança ainda não publicada, usar o padrão `dev-{branch}` no composer, não repositório
`path` local.

---

## Commits

Formato obrigatório, validado por hook — prefixos e regex em `context.yaml` (`commit:`).

O prefixo vale **também para merge commit**: o padrão do git (`Merge branch 'master' into CLS-123`) é
rejeitado. Escrever `CLS-123 Merge branch 'master' into CLS-123` em vez de recorrer a `--no-verify`.

A regra de não atribuição de IA está no global e vale aqui integralmente.

---

## SDD — o plugin, e o Jira como único lugar

Desde 2026-10-14 o SDD da Celesta é o plugin `celesta-engineering-playbook` (marketplace
`celesta-claude-marketplace`, instalado pelo `bootstrap.sh`). Quatro skills manuais, uma por fase:

| Fase | Skill | Escreve | Onde |
|---|---|---|---|
| spec | `/sdd-spec <parent>` | título + descrição em 5 seções | ticket pai |
| split | `/sdd-split <parent>` | uma sub-task **por repositório**, links Blocks | sub-tasks novas |
| plano | `/sdd-plan <sub-task>` | plano em 6 seções | descrição da sub-task |
| código | `/sdd-implement <sub-task>` | arquivos na branch `<KEY>`, testes verdes, `sdd-reviewer` limpo | working tree |

**Spec e plano não existem como arquivo.** Nada de `_specs/`, `_plans/` ou `.claude/commands/spec.md`
no serviço: o que ainda existir disso é legado, não fonte. Quem quer a spec lê a descrição do pai;
quem quer o plano lê a descrição da sub-task.

Constantes que as skills e eu usamos: `sdd:` no `context.yaml`. Precisam dos connectors Atlassian,
Notion (spec e split recusam sem ele) e GitHub. Cada fase relê o que precisa do Jira; se há
`/clear` entre elas é escolha por ticket (`router.md`).

Planejamento de épico multi-ticket continua fora das branches, em `tickets/<épico>/` — ver
`rules/deliverables.md`. O split organiza um pai; o que atravessa vários pais é do épico.

---

## Credenciais

Nenhuma credencial neste repositório. Todas vivem em `~/.claude-secrets/` — o índice está em
`context.yaml` (`secrets:`). Coleção de Postman versionada carrega o **nome** da variável com valor
vazio; o valor entra na environment do runner em tempo de execução.

Coleção ad-hoc, sem ticket, vai para a pasta local de coleções (`postman/`), nunca dentro do
repositório de um serviço.

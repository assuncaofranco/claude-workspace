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
   **Exceção:** a conversa de execução de uma story (`global/skills/ticket-story.md`, "Sessões") não
   roda `ticket-understand`: o entendimento chega da coordenação, por arquivo.
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
primeiro. Para mudança ainda não publicada, o serviço consome a biblioteca pela branch dela, nunca por
repositório `path` local:

- composer: `"lancasters/<lib>": "dev-<branch> as <próxima versão>"`;
- Go: `go get github.com/celesta-tech/<lib>@<branch>`, que vira uma pseudo-versão de um commit só, e
  por isso precisa ser refeito quando a branch da lib anda.

O pin fica até o épico ser aceito. Aí o lead faz o merge da biblioteca e anuncia a tag, e o dev troca
o pin pela tag num commit dele. Desde a 0.58 do playbook (#69), os revisores do SDD não apontam o pin
como achado; apontam pin para branch ou commit que não está no origin, ou manifesto sem o lock.

**No `sdd-release`:** o PR da biblioteca responde **não** à primeira pergunta (a própria referência
do skill dá "a library consumed from its branch" como exemplo): mergear a biblioteca gera tag, não
deploy. Mas a troca do pin tem de estar escrita para quem faz o deploy, então no release da sub-task
que **consome** a biblioteca a segunda pergunta recebe **sim**, com a ação manual antes do PR dela:
"mergear `<lib>#<PR>`, esperar a tag e trocar o pin `dev-<branch> as <versão>` pela tag, num commit no
PR da `<KEY>`". Sem isso o serviço vai para produção dependendo de uma branch. Caso real: CLS-4932 →
CLS-4933, 2026-11-12.

**O alias envelhece.** A biblioteca é tagueada por outros enquanto o pin espera: o `as 1.366` do CLS-4933
virou versão existente horas depois. Antes do review e de novo antes do release, conferir
`git tag --sort=-v:refname | head -1` da biblioteca e subir o alias se ele já existe.

---

## Commits

Formato obrigatório, validado por hook — prefixos e regex em `context.yaml` (`commit:`).

O prefixo vale **também para merge commit**: o padrão do git (`Merge branch 'master' into CLS-123`) é
rejeitado. Escrever `CLS-123 Merge branch 'master' into CLS-123` em vez de recorrer a `--no-verify`.

A regra de não atribuição de IA está no global e vale aqui integralmente.

---

## SDD — o plugin; spec no Jira, plano no repositório

Desde 2026-10-14 o SDD da Celesta é o plugin `celesta-engineering-playbook` (marketplace
`celesta-claude-marketplace`, instalado pelo `bootstrap.sh`). Quatro skills manuais, uma por fase, e
o `sdd-release`, que o implement chama no fim:

| Fase | Skill | Escreve | Onde |
|---|---|---|---|
| spec | `/sdd-spec <parent>` | título + descrição em 5 seções | ticket pai |
| split | `/sdd-split <parent>` | uma sub-task **por repositório**, links Blocks, todo list | sub-tasks novas |
| plano | `/sdd-plan <sub-task>` | plano em 7 seções + AC, Dependencies, Decisions | `.sdd/_plans/<KEY>.md` na branch `<KEY>`, num PR contra o master só com o arquivo |
| código | `/sdd-implement <sub-task>` | código em 3 passos: unit → review → Proteus (opcional) | mesma branch, push no PR do plano antes do review |
| release | `/sdd-release <sub-task>`, chamado pelo implement em toda run que fez push | o PR e as ações manuais na ordem de deploy | `releases/<PAI>.yaml` no `main` do `celesta-releases`; o link vai no campo Deployment instructions do pai **só se ele estiver vazio** |

O review são 8 agentes `sdd-reviewer-<aspecto>` em paralelo (contract, security, memory, performance,
db, tests, dead-code, quality), que postam os achados como comentários inline no PR, assinados com
emoji, e resolvem as threads lá; o PR ganha labels `sdd-review:<aspecto>` até ficar `sdd-reviewed`.
O implement termina com um comentário de veredito no PR. Toda fase posta o custo em dólar como
comentário no Jira: pai para spec e split, sub-task para plano e implement.

Desde a 0.47 (2026-11-03) não existe seção Postman tests no plano nem passo funcional: o passo
precisava da stack local inteira e ninguém rodava. O próprio playbook assume o custo: regressão que só
aparece pelas APIs do BO ou do gateway é pega depois do PR.

**A spec é a descrição do pai; o plano é o arquivo `.sdd/_plans/<KEY>.md` na branch da sub-task.**
A descrição da sub-task é só o todo list do split, nunca o plano. Desde a 0.42.0 (2026-10-28): antes
o plano morava na descrição da sub-task. `_specs/`, `_plans/` e `sdd/` na raiz de um serviço, ou
`.claude/commands/spec.md`, são do SDD antigo: legado, não fonte. O nome parece com `.sdd/_plans/`
e engana.

O `sdd-plan` cria a branch e abre o PR; o `sdd-implement` recusa sem eles e põe o código no mesmo PR.
Os testes de plataforma que o plano pede (seção Proteus tests) vão para `celesta-qaa-proteus`, em PR
próprio com a mesma key.

**Paralelo não é automático.** Cada `/sdd-plan` e `/sdd-implement` roda uma sub-task. O único paralelo
que o SDD faz sozinho são os 8 revisores, dentro de uma sub-task. Rodar sub-tasks em paralelo
("concurrent SDD") é a conversa abrir um agente por sub-task. Blocks é ordem de merge e de
implementação, não de plano: dois planos rodam juntos sempre que um não precisa ler o resultado do
outro (o 4934 do front não lê nada do 4933 do payment, embora o 4933 o bloqueie). O
`sdd-implement` de uma sub-task bloqueada só espera a branch da que bloqueia quando o código dela usa o
dela (pin de biblioteca, contrato novo); o skill não confere Blocks. O 4934 (front, lista própria) rodou
em paralelo com o 4933 numa segunda conversa de execução, 2026-11-12. Testado em 2026-11-11: o agente tem as skills do SDD e pode abrir subagentes, mas não fala
com o usuário; quando o SDD para e pergunta, o agente devolve a pergunta para a conversa que o abriu.
`sdd-spec` recusa Story: story com descrição pronta vai direto para `sdd-split`.

Constantes que as skills e eu usamos: `sdd:` no `context.yaml`. Precisam dos connectors Atlassian,
Notion (spec e split recusam sem ele) e GitHub. Cada fase relê a fonte (Jira e o arquivo do plano);
se há `/clear` entre elas é escolha por ticket (`router.md`).

Planejamento de épico multi-ticket continua fora das branches, em `tickets/<épico>/` — ver
`rules/deliverables.md`. O split organiza um pai; o que atravessa vários pais é do épico.

---

## Credenciais

Nenhuma credencial neste repositório. Todas vivem em `~/.claude-secrets/` — o índice está em
`context.yaml` (`secrets:`). Coleção de Postman versionada carrega o **nome** da variável com valor
vazio; o valor entra na environment do runner em tempo de execução.

Coleção ad-hoc, sem ticket, vai para a pasta local de coleções (`postman/`), nunca dentro do
repositório de um serviço.

# Roteador

Lido todo turno. Decide **o que carregar** — não contém regra nenhuma, só aponta.

Se um arquivo apontado aqui contradiz outro, isso é um defeito de estrutura: ver `rules/corpus.md`.

---

## 1. Classificar o input

O rótulo não basta; o que decide é o **sinal**. Na dúvida entre dois, perguntar antes de agir — errar
de contexto custa mais que uma pergunta.

| Sinal no input | Contexto | Carregar |
|---|---|---|
| Alerta colado: canal de alarme, PagerDuty, Datadog | **oncall** | `skills/oncall.md` + `rules/environment.md`. **Nunca** o fluxo de ticket. |
| "estamos em oncall", "começou/acabou meu turno", sem alerta | **turno** | `skills/oncall-shift.md` |
| Pede o resumo das alterações de um ticket, mesmo citando o id dele | **overview** | `skills/overview.md`. **Não** entra no fluxo de ticket: é leitura, o pedido é só o resumo. |
| Menciona id de ticket, ou descreve mudança a fazer | **ticket** | seção 2 abaixo |
| Story inteira comigo, sub-tasks em paralelo, ou repositório fora dos nossos | **story** | `skills/ticket-story.md`, que diz onde cada passo da seção 2 entra no SDD |
| Pede review, cita PR, ou traz comentário de review para resolver | **review** | seção 3 abaixo |
| Pergunta sobre o código, sem pedir mudança | **consulta** | nada; responder. `skills/explain.md` se pedir explicação; `skills/elaborate.md` se a explicação não funcionou por falta de base no domínio. |
| "o que fizemos ontem", pede a daily ou o resumo de um dia | **daily** | `skills/daily.md` |
| Pede para mudar como eu trabalho | **corpus** | `rules/corpus.md` **antes** de editar qualquer coisa |

Instrução concreta chegando junto da menção a um ticket (um comando git, um comentário para resolver)
**não** é sinal para pular o fluxo. O sinal é o ticket.

## 2. Ticket — a sequência

Cada passo é uma skill que se explica sozinha. A ordem importa em três pontos, nomeados no fim.

| # | Passo | Carregar |
|---|---|---|
| 1 | Entender a necessidade de negócio | `skills/ticket-understand.md` |
| 2 | Atualizar o master e ler o código do domínio que o ticket toca, do `origin/master` | `rules/environment.md` ("Master atualizado antes de começar") |
| 3 | Enumerar e classificar as variantes | `skills/ticket-matrix.md` |
| 4 | Spec, split por repositório e plano (matriz = critérios de aceitação) | fases de spec, split e plano do SDD do projeto (overlay) |
| 5 | Olhar o banco, somente leitura | `skills/db-query.md` |
| 6 | Gerar a doc, montar a coleção a partir dela | `skills/ticket-postman.md` |
| 7 | Implementar | fase de implementação do SDD do projeto + `skills/ticket-code.md` + `rules/scope.md` |
| 8 | Regerar a doc, rodar a coleção | `skills/ticket-postman.md` |
| 9 | Cruzar requisição, resposta real e schema | — |
| 10 | Diagnosticar divergência | `skills/ticket-postman.md` §7 |
| 11 | Conferir o dado no banco | `skills/db-query.md` |
| 12 | Lint e testes | `rules/environment.md` |
| 13 | Review | seção 3 |
| 14 | Instruções de deploy, nos PRs e na pasta do ticket | `skills/deploy-instructions.md` |
| 15 | **Perguntar** se testamos em preprod | `skills/preprod-test.md` |
| 16 | Entregar para o usuário testar |

**Três lugares onde a ordem é o valor:**

- **3 antes de 4** — os critérios derivam da enumeração. Spec escrito primeiro ganha critérios só para
  as variantes de que lembramos, que é como o ticket volta rejeitado.
- **6 antes de 7** — montar a coleção antes de implementar transforma a doc em teste, não em
  auditoria. Num bug, o passo 6 já reproduz.
- **8 depois de 7, repetido** — a doc do que o ticket cria só existe depois do código.

**Onde o SDD do projeto não cobre sozinho.** As fases do SDD executam o que o artefato anterior diz, e
nada mais. Então o **resultado** do que este fluxo tem e elas não têm precisa estar escrito no
artefato, ou se perde. O resultado, não a ferramenta: o artefato é do time e não cita o nosso fluxo
(`rules/writing.md`, "O nosso fluxo não aparece no artefato do time").

- os critérios que saem da matriz (3) entram nos critérios de aceitação da spec, como critérios
  comuns. A tabela da matriz, com classes e justificativas, fica na pasta do ticket;
- as checagens da coleção (6) para as células afetadas que o contrato do serviço observa entram na
  seção de teste de plataforma do plano (na Celesta, Proteus tests; ver overlay), descritas como
  requisição e resultado esperado — nunca na estratégia de teste unitário, que o playbook reserva
  ao teste do próprio repositório. É dessa seção que a fase de implementação escreve os testes do
  time. O resto fica só na coleção, do nosso lado, que roda nos passos 8 e 15: o SDD do projeto
  não tem passo funcional (ver overlay), então regressão que só aparece pelas portas de entrada só
  a coleção pega antes do merge;
- as regras de `ticket-code` que o plano precisa (critério sem código, migration, constante na
  biblioteca) entram nas tarefas do plano — quem implementa não improvisa além delas.

Os revisores automáticos da fase de implementação **não** substituem o passo 13: eles leem diff, plano
e spec, não a matriz contra a coleção nem a doc contra a resposta real.

`/clear` entre fases do SDD é escolha por ticket, não regra. **[nosso]** — o playbook não pede.
Ticket pequeno e mecânico: manter o histórico, porque a sessão já leu o repositório e achou as
armadilhas; o que o contexto puser a mais aparece no diff, que os revisores do SDD e o passo 13 leem.
Ticket grande, ou plano que discutiu alternativas descartadas: `/clear`, porque o contexto pesa em
todo turno e a alternativa descartada pode voltar no código. Nos dois casos a fase relê a fonte (o
Jira e o arquivo do plano), nunca confia no chat. Decisão do Lucas, 2026-10-21 (CLS-1283).

**Modelo por fase. [nosso]** Planejar é Opus: entender, matriz, spec, split, `sdd-plan` até o plano no
PR, gate 1 e review da story inteira. Executar é Sonnet: `sdd-implement`, o laço com os revisores, CI e
`sdd-release`. Na conversa, `/model`; agente aberto para executar leva `model: sonnet`. O Sonnet
para e pergunta quando um achado de revisor pede mudar o plano ou a spec, ou quando aparece um plano
ainda não revisto (sub-task criada no meio da execução): isso volta para o Opus. **Por quê:** o
julgamento está no plano. Com o plano aprovado, o que sobra é seguir o texto, e os tokens acabaram no
meio do CLS-3316 com quatro stories abertas. Decisão do Lucas, 2026-11-16.

O passo 14 nunca é pulado, nem quando o ticket parece não ter ordem: quem faz o deploy não é o Lucas,
e o que não estiver escrito não existe para quem aperta o botão.

O passo 15 é **pergunta, nunca silêncio**. Se sim, roda todas as células afetadas, não um caminho
feliz — verificação parcial de mudança multi-variante é o que gerou as rejeições que isto evita.

O passo 1 nunca é pulado.

## 3. Review — um só fluxo, atribuição muda os passos

O *como revisar* é o mesmo nos meus tickets e nos dos outros. O que muda é quais passos rodam:

| Atribuição | Passos |
|---|---|
| Dev (ticket meu) | 1-16 |
| Revisor (ticket de outro) | 1, 2, 4 (lê a matriz existente, **não** reconstrói), 13 |
| Testador / QA | 1-6, 8-9, 11, 15 |

Carregar: `skills/ticket-review.md` + `rules/review-lens.md` + `rules/writing.md` (comentário de PR
tem voz própria).

## 4. Sempre carregado, independente de contexto

`rules/writing.md` — como eu escrevo, e a regra de não atribuição de IA. Vale em toda saída.

**Migration — carregado sempre que houver DDL.** Plano, diff ou review com `CREATE`, `ALTER`, `DROP`,
`RENAME`, índice ou chave estrangeira: carregar `rules/migrations.md` **antes** de escrever o plano,
a migration ou o veredito. Vale em qualquer contexto da seção 1 e em qualquer passo da seção 2
(4, 7, 13 e 14 são onde ela mais pesa). Nenhum DDL sobre tabela existente passa sem a análise com
dado de produção.

## 5. Services — regra compartilhada, uma definição só

| Arquivo | O que decide |
|---|---|
| `rules/migrations.md` | DDL que trava tabela: listar as tabelas, medir em produção, teto de espera, e o que fazer se houver risco |
| `rules/scope.md` | o que está dentro e fora do escopo de um ticket, e a única exceção |
| `rules/environment.md` | stack quebrada, cache velho, quando `make init` |
| `rules/review-lens.md` | de onde tirar a verdade num review, e como pesar um achado |
| `rules/writing.md` | comunicação, comentário de PR, zero atribuição de IA |
| `rules/deliverables.md` | onde cada artefato é salvo |
| `rules/secrets.md` | credencial nunca entra no git |
| `rules/jira.md` | o que escrevo no Jira sem perguntar (board, marcas do SDD) e o que espera pedido |
| `rules/corpus.md` | como mudar estas regras sem criar contradição |

O contexto do projeto (serviços, containers, caminhos, credenciais) fica no overlay dele, não aqui.

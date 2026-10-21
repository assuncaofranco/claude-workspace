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
| Menciona id de ticket, ou descreve mudança a fazer | **ticket** | seção 2 abaixo |
| Pede review, cita PR, ou traz comentário de review para resolver | **review** | seção 3 abaixo |
| Pergunta sobre o código, sem pedir mudança | **consulta** | nada; responder. `skills/explain.md` se pedir explicação. |
| "o que fizemos ontem", pede a daily ou o resumo de um dia | **daily** | `skills/daily.md` |
| Pede para mudar como eu trabalho | **corpus** | `rules/corpus.md` **antes** de editar qualquer coisa |

Instrução concreta chegando junto da menção a um ticket (um comando git, um comentário para resolver)
**não** é sinal para pular o fluxo. O sinal é o ticket.

## 2. Ticket — a sequência

Cada passo é uma skill que se explica sozinha. A ordem importa em três pontos, nomeados no fim.

| # | Passo | Carregar |
|---|---|---|
| 1 | Entender a necessidade de negócio | `skills/ticket-understand.md` |
| 2 | Ler o código do domínio que o ticket toca | — |
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
- as checagens da coleção (6) entram na estratégia de teste do plano, descritas como requisição e
  resultado esperado. A coleção fica do nosso lado e roda nos passos 8 e 15;
- as regras de `ticket-code` que o plano precisa (critério sem código, migration, constante na
  biblioteca) entram nas tarefas do plano — quem implementa não improvisa além delas.

O revisor automático da fase de implementação **não** substitui o passo 13: ele lê diff, plano e spec,
não a matriz contra a coleção nem a doc contra a resposta real.

`/clear` entre fases do SDD é escolha por ticket, não regra. **[nosso]** — o playbook não pede.
Ticket pequeno e mecânico: manter o histórico, porque a sessão já leu o repositório e achou as
armadilhas; o que o contexto puser a mais aparece no diff, que o `sdd-reviewer` e o passo 13 leem.
Ticket grande, ou plano que discutiu alternativas descartadas: `/clear`, porque o contexto pesa em
todo turno e a alternativa descartada pode voltar no código. Nos dois casos a fase relê a fonte (o
Jira), nunca confia no chat. Decisão do Lucas, 2026-10-21 (CLS-1283).

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

## 5. Services — regra compartilhada, uma definição só

| Arquivo | O que decide |
|---|---|
| `rules/scope.md` | o que está dentro e fora do escopo de um ticket, e a única exceção |
| `rules/environment.md` | stack quebrada, cache velho, quando `make init` |
| `rules/review-lens.md` | de onde tirar a verdade num review, e como pesar um achado |
| `rules/writing.md` | comunicação, comentário de PR, zero atribuição de IA |
| `rules/deliverables.md` | onde cada artefato é salvo |
| `rules/secrets.md` | credencial nunca entra no git |
| `rules/corpus.md` | como mudar estas regras sem criar contradição |

O contexto do projeto (serviços, containers, caminhos, credenciais) fica no overlay dele, não aqui.

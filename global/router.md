# Roteador

Lido todo turno. Decide **o que carregar** — não contém regra nenhuma, só aponta.

Se um arquivo apontado aqui contradiz outro, isso é um defeito de estrutura: ver `rules/corpus.md`.

---

## 1. Classificar o input

O rótulo não basta; o que decide é o **sinal**. Na dúvida entre dois, perguntar antes de agir — errar
de contexto custa mais que uma pergunta.

| Sinal no input | Contexto | Carregar |
|---|---|---|
| Veio de canal de alarme, PagerDuty, Datadog, ou "estou de oncall" | **oncall** | `skills/oncall.md` + `rules/environment.md`. **Nunca** o fluxo de ticket. |
| Menciona id de ticket, ou descreve mudança a fazer | **ticket** | seção 2 abaixo |
| Pede review, cita PR, ou traz comentário de review para resolver | **review** | seção 3 abaixo |
| Pergunta sobre o código, sem pedir mudança | **consulta** | nada; responder. `skills/explain.md` se pedir explicação. |
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
| 4 | Spec e plano (matriz = critérios de aceitação) | template do serviço + `rules/deliverables.md` |
| 5 | Olhar o banco, somente leitura | `skills/db-query.md` |
| 6 | Gerar a doc, montar a coleção a partir dela | `skills/ticket-postman.md` |
| 7 | Implementar | `skills/ticket-code.md` + `rules/scope.md` |
| 8 | Regerar a doc, rodar a coleção | `skills/ticket-postman.md` |
| 9 | Cruzar requisição, resposta real e schema | — |
| 10 | Diagnosticar divergência | `skills/ticket-postman.md` §7 |
| 11 | Conferir o dado no banco | `skills/db-query.md` |
| 12 | Lint e testes | `rules/environment.md` |
| 13 | Review | seção 3 |
| 14 | **Perguntar** se testamos em preprod | `skills/preprod-test.md` |
| 15 | Entregar para o usuário testar |

**Três lugares onde a ordem é o valor:**

- **3 antes de 4** — os critérios derivam da enumeração. Spec escrito primeiro ganha critérios só para
  as variantes de que lembramos, que é como o ticket volta rejeitado.
- **6 antes de 7** — montar a coleção antes de implementar transforma a doc em teste, não em
  auditoria. Num bug, o passo 6 já reproduz.
- **8 depois de 7, repetido** — a doc do que o ticket cria só existe depois do código.

O passo 14 é **pergunta, nunca silêncio**. Se sim, roda todas as células afetadas, não um caminho
feliz — verificação parcial de mudança multi-variante é o que gerou as rejeições que isto evita.

O passo 1 nunca é pulado.

## 3. Review — um só fluxo, atribuição muda os passos

O *como revisar* é o mesmo nos meus tickets e nos dos outros. O que muda é quais passos rodam:

| Atribuição | Passos |
|---|---|
| Dev (ticket meu) | 1-15 |
| Revisor (ticket de outro) | 1, 2, 4 (lê a matriz existente, **não** reconstrói), 13 |
| Testador / QA | 1-6, 8-9, 11, 14 |

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

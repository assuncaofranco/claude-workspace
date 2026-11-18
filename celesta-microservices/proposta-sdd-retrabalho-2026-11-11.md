# Proposta: retrabalho no SDD (2026-11-11)

Plugin 0.56.0. Proposta, não regra: cada mudança no nosso corpo passa por `rules/corpus.md` antes de
ser editada.

## 1. O que o SDD registra hoje, e onde o time vê

| Sinal | Onde fica | Origem |
|---|---|---|
| Custo por fase, em dólar, com `(2 runs)` quando a fase reroda | comentário no Jira: pai (spec, split), sub-task (plan, implement) | todas as fases, desde a 0.53 (#72) |
| Rodada do review, `round 2`, `round 3` | assinatura de cada comentário inline no PR | `sdd-implement` passo 2 |
| Aspecto com thread aberta | label `sdd-review:<aspecto>` no PR; `sdd-reviewed` só quando limpo | idem |
| Discordância depois de 3 rodadas | thread aberta no PR, com os dois lados | idem |
| Plano errado | commit `<KEY>: plan amended — <motivo>` no PR | `sdd-plan` na reemissão |
| O que o implement fez além do plano | parágrafo "Beyond the plan" do veredito no PR | `sdd-implement`, desde a 0.55 (#82) |
| Ordem de deploy mudada | commit `moved to group n` em `celesta-releases` | `sdd-release` |

Detalhe que pesa: o custo sai do transcript da **sessão**. Uma fase rodada no fim de uma sessão
longa (understand, matriz, banco) paga o contexto inteiro em cada mensagem, e o próprio
`step-cost.md` admite que o número fica acima do que a fase custaria sozinha.

## 2. De onde vem o retrabalho

Os commits `plan amended` da org (`gh search commits "plan amended" --owner celesta-tech`) mostram
quatro causas:

| Causa | Exemplos | Fase que deveria ter pego |
|---|---|---|
| O plano não bate com o código ou com o ambiente: wiring de teste, contagens, versões, rebase | CLS-4163 *test wiring* (nosso), CLS-4415 ×7, CLS-4417 *rebase on master* | plano |
| O review pediu o que o plano não previa | CLS-4210 *review round 1/2*, CLS-4140 *test the missing-field row* | plano |
| Dependência de biblioteca ainda em branch | CLS-4208, CLS-4133 | split e plano |
| Decisão nova de fora | CLS-4322 *at Virgile's request* (nosso) | nenhuma: é legítimo |

A quarta causa não é erro. As três primeiras são.

## 3. Onde está o problema estrutural

No nosso router, a verificação forte (coleção, schema, banco, lint, review: passos 8 a 13) vem
**depois** do passo 7. Mas o passo 7 agora faz push, roda os 8 revisores no PR, posta o veredito, o
custo e o manifesto. Tudo o que achamos depois dele vira uma segunda run, uma emenda do plano ou
commit depois do `sdd-reviewed`, e tudo isso fica visível.

Existe uma janela: o `sdd-implement` termina o passo 1 (unit verde), **para e pede o ok do push**
antes do review (`reviewing-the-diff.md`, "The code has to be on the pull request first"). Até esse
ok, nada saiu da máquina. Qualquer correção feita ali ainda é a run 1, rodada 0.

## 4. Pontos de checagem, por fase

| Antes de | Checagem | Evita | Nosso arquivo |
|---|---|---|---|
| qualquer fase | plugin atualizado (`claude plugin update`): a fase com plugin velho para e pede rerun | run perdida | overlay |
| qualquer fase | sessão nova, com handoff curto (key + arquivos da pasta do ticket) | custo inflado pelo contexto | router (conflita com a regra do `/clear`, ver §6) |
| spec | matriz assinada; as perguntas do lote respondidas a partir dela | spec reescrita, critério faltando | já existe (router 3→4) |
| split | lista de repositórios e ordem de deploy derivadas por nós; sub-task de cleanup e de compatibilidade; biblioteca antes do consumidor | sub-task faltando, `Blocks` errado, manifesto movido | `deploy-instructions` (derivação adiantada) |
| implement | **review do PR do plano por nós**, com 3 checagens: (a) todo `File Changes` existe e todo comando ou teste citado roda hoje (wiring, versões); (b) cada AC tem tarefa e teste; (c) o plano já pede o que os revisores cobram: migration reversível com índice (db), cleanup que o ticket deixa (dead-code), teste que falha se reverter (tests), paginação e N+1 (performance) | emenda no implement, rodadas 2 e 3 | `ticket-review` como autor (novo modo) |
| implement | branch atualizada com o master; `make init` depois da troca; baseline do Proteus no master verde | emenda *rebase*, falso vermelho no passo 1 ou 3 | `rules/environment.md` |
| **push do implement** | no ok do push: rodar a coleção (8 a 11) e `make lint` na árvore local; o que falhar é corrigido ali, ainda na run 1 | segunda run, rodada extra, "Beyond the plan" | router: 8 a 12 passam para dentro do 7 |
| fim do implement | respostas do `sdd-release` vindas da derivação | commit `moved to group n` | `deploy-instructions` |
| nosso review (13) | ler as threads e o veredito antes; não repetir o que os agentes já disseram | — | `ticket-review` |

O que sobra depois do push (preprod, passo 15) continua depois, porque precisa do deploy da branch.

## 5. Registro nosso

Cada vez que algo da tabela 1 acontecer num ticket nosso, uma linha em
`tickets/<KEY>/retrabalho.md`: o sinal, a causa, e qual checagem da §4 deveria ter pego (ou "nenhuma",
e aí falta uma). A cada poucos tickets, o que se repetir vira regra pelo `corpus.md`, ou vira
`/sdd-improve` quando a falha for do playbook e não nossa.

## 6. Decisões tuas antes de editar

1. **Sessão nova por fase do SDD.** Conflita com o router hoje: "ticket pequeno e mecânico: manter o
   histórico" (2026-10-21). Substituir ou exceção nomeada?
2. **Passos 8 a 12 dentro do 7, na pausa do push.** Muda a ordem do router.
3. **Review do plano por nós antes do implement.** Passo novo, entre 4 e 7.
4. **Derivação da ordem de deploy antes do split.** Pendente desde a análise do `sdd-release`.
5. **Assinatura com emoji nos comentários do review do SDD.** Conflita com `writing.md`. Exceção
   nomeada para o processo do time, ou não?
6. **Instruções desatualizadas pela 0.47+.** Seção Postman do plano, passo funcional,
   `sdd-reviewer`, label: corrigir no router, no overlay e no `context.yaml`.

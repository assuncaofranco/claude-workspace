---
description: Fluxo para uma story inteira comigo, sub-tasks em paralelo, ou repositório fora dos nossos. O SDD do time roda inteiro e não se altera; nós agimos só nos dois pontos em que ele para e pergunta, antes de cada push, para que o que chega ao PR já esteja limpo.
argument-hint: <story ou sub-task>
---

# ticket-story

Entra quando a story inteira é minha, com as sub-tasks rodando em paralelo, ou quando o repositório
não é um dos nossos. O fluxo de ticket (`router.md` §2) continua valendo para todo o resto; este
arquivo diz **onde** cada passo dele se encaixa no SDD quando são três sub-tasks de uma vez, e o que
muda quando o domínio não é nosso.

**Por quê.** 2026-11-02 a liderança anunciou o SDD concorrente (um dev pega a story e roda as
sub-tasks em paralelo). 2026-10-30 o Lucas entrou no `global-write-team` (64 repositórios) e em
2026-11-11 recebeu seis tickets do Team A. Em repositório que nunca rodamos, o erro que chega ao PR
fica registrado como thread dos revisores e como custo postado no Jira. O SDD não se altera; o que
podemos é chegar limpo em cada push.

## O princípio: dois pontos, e só eles

O SDD para e pergunta duas vezes por sub-task. São os únicos lugares onde entramos:

| Gate | Onde o SDD para | O que fazemos antes do "sim" |
|---|---|---|
| 1 · plano | `sdd-plan`, entre mostrar o rascunho (passo 10) e escrever/push (passo 11) | os planos **da story inteira** revisados juntos: contrato entre os serviços, critérios da matriz presentes, nada fora do escopo |
| 2 · código | `sdd-implement`, pedido de push antes do passo 2 (review) | matriz célula a célula com Onde e Prova, coleção rodada, doc × resposta real; correção **dobrada no commit de implementação** |

Depois do push, nada se apaga: thread de revisor e commit no PR são do time. Correção de gate 2 é
amend ou squash local (`git reset --soft <commit do plano>`, um commit), nunca commit "fix" por cima.

## Sequência

| # | Passo | Carregar |
|---|---|---|
| 0 | Baseline do repositório: master atualizado, `make init` no master, testes verdes, `CLAUDE.md` lido. Resultado em `memory/projects/<repo>/` | `rules/environment.md` |
| 1 | Entender o produto, story inteira | `skills/ticket-understand.md`, exceção "domínio que não é nosso" |
| 2 | Matriz da story inteira, todas as sub-tasks | `skills/ticket-matrix.md` |
| 3 | Spec: ver "Spec que não é nossa" | SDD |
| 4 | Split, se não existe | SDD |
| 5 | `sdd-plan` por sub-task, até o rascunho. **Gate 1** | `rules/review-lens.md` |
| 6 | Banco e coleção, por sub-task | `skills/db-query.md`, `skills/ticket-postman.md` |
| 7 | `sdd-implement` por sub-task, até o pedido de push. **Gate 2** | `skills/ticket-review.md` §4 e §8, `rules/scope.md` |
| 8 | Rodada dos revisores do SDD, sub-tasks em paralelo | SDD |
| 9 | `sdd-release`, instruções de deploy, preprod (pergunta) | `skills/deploy-instructions.md`, `skills/preprod-test.md` |

## Spec que não é nossa

Um pai já em Split tem spec de outro. Três saídas, nesta ordem:

1. não existe spec → `sdd-spec`, nossa;
2. existe e a matriz achou buraco → propor a mudança de critério ao dono da story (texto curto, o
   Lucas posta), e não planejar em cima do buraco;
3. o Lucas autoriza **expressamente** editar → editar pela fase do SDD, nunca à mão.

Decisão do Lucas, 2026-11-11.

## Sessões

- **Coordenação**, uma conversa: produto, matriz, os dois gates, decisões e problemas do processo.
  Faz os gates **a partir do git e do transcript da execução**, nunca do que foi dito
  (`rules/review-lens.md`). Nunca roda `/sdd-*`.
- **Execução**, uma conversa só: roda o SDD e a parte mecânica (baseline, banco, coleção). Sub-tasks
  sem dependência vão para agentes, cada um parando onde o SDD para. Não roda `ticket-understand` nem
  `ticket-matrix`: recebe o resultado deles por arquivo.
- O "sim" é dado na execução só depois que a coordenação fechou o gate, e só pelo Lucas.
- As duas se falam por arquivo, na pasta do sprint ou da story: `plan.md`, `decisions.md`,
  `process-log.md`, `<KEY>/matrix.md`.

Decisão do Lucas, 2026-11-11. Estende `memory/feedback_implement_in_separate_session.md`.

**Variante só SDD** (15-Beedrill, 2026-11-12, a empresa testando o formato): a execução recebe só
`/sdd-*` e correções em inglês; nada do nosso fluxo entra lá. A coordenação vira avaliação: confere
cada saída e registra antes do próximo passo. Como roda: `celesta-microservices/sprints/15-beedrill/index.md`.
Se o formato ficar, esta seção é reescrita a partir do `evaluation.md` de lá.

**No processo inteiro por SDD, todas as sub-tasks são nossas, front incluído** (backoffice-front, BO,
gateway, segment, de qualquer time). O time dono do repositório só aprova e faz o merge. Confirmado pelo
Mykyta, que rodou um épico inteiro assim (2026-11-12). Componente A-Team e assignee o Lucas em todas,
mesmo quando o PO acrescenta o componente do dono no pai.

### O que conferir em cada parada do SDD

Aprendido no 15-Beedrill (CLS-4779), 2026-11-12. Cada item custou uma volta.

| Parada | Conferir |
|---|---|
| Antes de tudo | master atualizado e código lido do `origin/master` (`rules/environment.md`) |
| Toda parada | o SDD não move o board. Sub-task: plano no PR → Planned; implement rodando → In Progress; `sdd-reviewed` + CI verde → To review, sem review nosso por sub-task (Lucas, 2026-11-16, CLS-1214: o review da story inteira, abaixo, pega o que o de uma sub-task não vê); Implemented só **depois** do review humano (Lucas, 2026-11-12). Pai: Implementing quando a primeira sub-task começa. Essas transições vão sem perguntar (`rules/jira.md`) |
| `sdd-split` | componente = time de quem faz (A-Team), não o dono do repositório; título mantém o prefixo do dono (`{B}`, `{F}`); assignee o Lucas nas sub-tasks, pai intocado. O split erra o componente toda vez que a story toca repositório de outro time: corrigir antes do "sim" |
| `sdd-plan`, rascunho | além das perguntas, ler Architecture & Design atrás de escolha **sem precedente** no código (a trava de transação do CLS-4933 passou porque não era pergunta). Escolha nova: seguir o padrão do código ou registrar em Decisions com motivo e quem decidiu |
| `sdd-plan`, rascunho | comparar com o fluxo dos casos equivalentes que já existem (ex.: os outros provedores com refund automático) antes de aceitar uma recomendação que "conserta" algo: o padrão existente é a régua, e o que for igual a ele não precisa ser defendido |
| `sdd-plan`, paralelo | Blocks ordena merge e implementação, não plano: planos que não leem o resultado um do outro rodam juntos em agentes (overlay, seção SDD) |
| `sdd-implement`, antes | `make init` no repositório; clone com arquivo "modificado" que ninguém tocou pode ser colisão de maiúscula no Mac (memória do projeto), não alteração |
| `sdd-implement`, antes, plano com seção Proteus | o `celesta-qaa-proteus` exige `.env` local, além de OAS e SQL do serviço antes da primeira edição. O id do Qase sai da primeira execução. Sem isso o implement para no meio. **Não rodamos Proteus local** (Lucas, 2026-11-12): avisar já no início do implement que os testes vão para a branch de mesmo nome no proteus e o CI valida |
| `sdd-implement`, push | diff igual ao plano, nada fora; sem atribuição de IA na mensagem |
| `sdd-implement`, fim da revisão | Desde o CEL-9751 o CI de branch não roda sozinho. Disparar `gh workflow run ci.yml -R celesta-tech/<repo> --ref <KEY>` depois do último push, não a cada um. O job `proteus` roda **dentro** do CI do serviço; o repositório de QA não tem CI de PR |
| Todas as sub-tasks com `sdd-reviewed` (as já entregues ficam em To review) | review da story inteira por um agente sem contexto: contratos entre os repositórios, caminhos de dinheiro, documentos (planos, corpo dos PRs, manifesto), estados intermediários do deploy. Pega o que o review por PR não vê (CLS-4779: ordem do proteus, corpo dos PRs, refund sem `state`) |
| `sdd-release` | PR de biblioteca: não entra; a ação manual de troca do pin vai no release de quem consome (overlay, "Bibliotecas compartilhadas") |

## Decisões de 2026-11-11

| Pergunta | Decisão |
|---|---|
| Produto sem o Lucas conhecer o domínio | discutir: eu trago código e Notion, ele pergunta o que não faz sentido; a classificação continua dele, depois da conversa |
| Spec de outro com buraco | propor ao dono, ou editar com autorização expressa |
| Planos de uma story | revisados juntos antes de qualquer push |

## O que ainda não sabemos

Se o provedor do payment roda local; quem é o PO do Team A; se o TL do A (Viorel) espera coleção e
preprod nossos ou só o PR. Perguntar quando o passo chegar, não antes.

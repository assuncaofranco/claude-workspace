# Avaliação do formato só SDD — 15-Beedrill

Um bloco por passo, escrito antes do próximo comando. Serve de feedback se alguém pedir: o que o SDD
acertou, o que errou, quanto custou corrigir.

Erro se classifica por onde nasceu: **spec** (o pai pediu errado ou faltou), **fase** (a skill leu
certo e produziu errado), **repo** (regra ou ambiente do repositório), **nosso** (a correção que
mandamos estava errada).

## Modelo

### <#> `<comando>` — <data>

- Saída: o que produziu (plano, sub-tasks, commits, PR), com link.
- Custo: o que a fase postou no Jira.
- Erros: um por linha, com a origem (spec / fase / repo / nosso).
- Correção enviada: o texto em inglês, exatamente como foi colado.
- Depois da correção: resolveu ou não, e quantas voltas.
- Leitura: uma frase sobre o formato, não sobre o ticket.

---

### 1 `/sdd-split CLS-4779` — 2026-11-12

- Saída (proposta, antes de criar): 3 sub-tasks — constants (A, 1 SP) → payment (A, 5 SP) → backoffice-front (F, 2 SP), Blocks 1→2→3; pai ganha A-Team + F-Team, label `sdd-split`, Ready → Split.
- Conferido no código: `PaytechProvider::doRefund` não implementado; payment valida por `PAYMENT_METHODS_AUTOMATIC_REFUND` (provedor × método) ou `PROVIDER_NAMES_AUTOMATIC_REFUND` (provedor inteiro) em `RefundController::isMethodAllowedAutomaticRefund`; a lista por método é a certa para "só cartão". O front decide `canBeAutomaticRefund` sozinho, então precisa da sub-task dele. BO só repassa `refundType`. Gateway fora.
- Erros: nenhum.
- Correção enviada: nenhuma.
- A sub-task 3 (front, F) também é nossa: fazemos todas as sub-tasks, de qualquer time.
- Erro (origem **fase**, conflito com o formato): o split tira o componente do dono do repositório
  (tabela do Notion), então pôs F-Team na 3. No formato novo o componente segue quem faz (A).
  Correção enviada antes do "sim": criar a 3 com A-Team, título `{F}` mantido; o pai fica só com A-Team.
- Desfecho: a correção não foi preciso mandar; a execução criou as três com A-Team (CLS-4932, 4933,
  4934). O título da 4934 saiu `{A}`; voltado para `{F}` aqui. Assignee posto aqui nas três.
- Leitura do formato: o `sdd-split` assume que repositório = time. Cross-team, toda story com
  repositório de outro time vai precisar da mesma correção. Candidato a feedback para o playbook.

### Entre 1 e 2 — master local velho (2026-11-12)

- Os oito repositórios tinham o master local de 24 a 680 commits atrás do origin. O SDD não sofre:
  `sdd-plan` lê e ramifica de `origin/master`. Quem sofreu foi a avaliação: as conferências de código
  daqui liam a árvore de trabalho. Refeitas contra `origin/master`, todas valem. Masters atualizados
  por fast-forward.
- Virou regra em `global/rules/environment.md` ("Master atualizado antes de começar"), apontada no
  passo 2 do `router.md`: fetch e fast-forward do master no início, e conferência de código sempre
  do `origin/master`.
- Pendente para o `sdd-implement`: rodar `make init` no repositório antes, porque container e vendor
  foram montados em branches antigas. Ver se o implement faz isso sozinho.

### 2 `/sdd-plan CLS-4932` (constants) — 2026-11-12, gate 1

- Saída (rascunho): Paytech → `CARD_PAYMENT_METHODS` em `PAYMENT_METHODS_AUTOMATIC_REFUND`; teste que
  fixa a entrada e exclui applepay, googlepay, oct; não mexe em `PROVIDER_NAMES_AUTOMATIC_REFUND`.
- Conferido: `CARD_PAYMENT_METHODS` são os seis cartões; a escolha da lista por método é a certa.
- Achado útil do plano: o BO já expõe esse mapa no endpoint de constantes
  (`paymentMethodsAutomaticRefund`), mas o front não usa: `TransactionRefundModal.js:37` repete a
  lista à mão. Avaliar no gate da 4934 se o front deveria ler do endpoint (fim da duplicação) ou só
  acrescentar a Paytech (escopo mínimo).
- Erros: nenhum. "Decisions: None" é seção vazia do template; não vale correção.
- Processo: a execução tratou Blocks como impedimento para planejar em paralelo, porque a regra que
  escrevi no overlay dizia isso. Corrigida no overlay: Blocks ordena merge e implementação, não plano.
  Origem **nosso**.
- Desfecho: plano escrito, PR celesta-constants#632, custo split + plano = $3.72.

### 3 `/sdd-plan CLS-4933` (payment) e `/sdd-plan CLS-4934` (front), em agentes paralelos — gate 1

- Funcionou: dois agentes, cada um parou no passo 10 sem escrever nada; a execução juntou as
  perguntas num lote só (7) e salvou os rascunhos em arquivo.
- 4933, perguntas com peso real:
  - Q2 (timeout de refund pendente): conferido no `origin/master`. `PaytechProvider::doTimeout` marca
    `timeout` sem consultar a Paytech e `STATUSES_FAILED` inclui `timeout`, então
    `RefundController::isRefunded` libera um segundo refund. Risco de reembolso duplo. A recomendação
    (consultar a Paytech antes do timeout, só para refund) é a certa. Achado que nenhum de nós tinha.
  - Q4 (refund parcial): decisão com cara de produto, mas o BO já aceita parcial nos outros
    provedores; seguir o padrão e conferir na sandbox.
  - Q2 revista a pedido do Lucas (sentiu red flag). O que a revisão mudou:
    - Erro meu (origem **nosso**): eu disse que só a Paytech dava timeout sem consultar. São cinco
      (Paytech, Funanga, Globalcharge, Tpf, Yowpay). O que vale: os três provedores que têm refund
      automático hoje (Centrobill, PaymentIQ, Ezeewallet) consultam antes.
    - B não fecha o risco, só reduz: se a Paytech ainda disser PENDING no timeout (padrão de payin,
      900 s), o refund vira `timeout`, final, o webhook posterior é ignorado e `isRefunded` libera
      outro refund. Mesmo resíduo dos outros três. Falta saber quanto tempo um refund fica PENDING
      na Paytech: conferir na sandbox.
    - Lacuna do rascunho (origem **fase**): na consulta do timeout, estado não mapeado
      (`AWAITING_APPROVAL`) faz `mapPaytechStateToStatus` lançar; o refund nunca dá timeout e loga
      erro a cada rodada. O rascunho tratou o estado não mapeado só no `doRefund`.
    - Confirmado: a mudança só alcança transação tipo refund com id da Paytech; depósito e payout
      ficam iguais. O loop do `TransactionsTimeoutCommand` captura exceção por transação.
    - O `RefundJob` vai para a wallet antes da resposta do provedor; a wallet debita o saldo na hora.
      Erro meu (origem **nosso**), corrigido: eu disse que em falha o saldo não voltava. Volta. O
      payment manda `TransactionUpdateJob` em toda mudança de status, e a wallet
      (`PaymentTransactionJobHandler`, ramo `TYPE_REFUND`) faz `refundRollback` quando o refund cai em
      fraud, failure ou timeout. Eu tinha procurado só no `TransactionStatusSubscriber`.
    - Consequência certa, que o Lucas viu antes de mim: refund em `timeout` devolve o saldo; se a
      Paytech concluir depois, o webhook é ignorado e o player fica com o saldo e com o dinheiro no
      cartão. A B reduz (pergunta antes), não elimina. É o mesmo resíduo dos três provedores
      automáticos de hoje, que também consultam antes do timeout de 15 min. Decisão do Lucas: seguir o
      padrão deles. Sem pergunta ao Viorel.
    - Docs da Paytech (baixadas pela execução): webhook só em estado final (COMPLETED, DECLINED,
      CANCELLED, AUTHORIZED); PENDING não é final. Nada sobre quanto tempo um refund fica pendente,
      retentativa de webhook, nem o que é `AWAITING_APPROVAL`. Sandbox ou suporte da Paytech.
- 4934 escrito: PR backoffice-front#2282. 4933 parado: o clone do payment aparece com
  `tests/Stubs/DdTrace.php` modificado. Não é alteração: o repositório versiona `DdTrace.php` e
  `ddtrace.php` (CLS-3511, 2026-10-22), e o macOS não distingue maiúscula; o checkout escreve os dois
  no mesmo arquivo e o último ganha. Apareceu no fast-forward do master que fiz às 10:55. Worktree não
  resolve (mesmo disco). Pode seguir: o commit do plano só adiciona o arquivo do plano.
  Risco para o `sdd-implement` do 4933: localmente só um dos dois stubs existe, e testes que usam o
  outro podem quebrar no Mac sem ser regressão.
- Desfecho do gate 1 (conferido nos branches do origin): planos publicados — constants#632,
  payment#1431, backoffice-front#2282; um commit `CLS-XXXX: plan` cada, só o arquivo do plano, sem
  atribuição em commit nem PR. Os dois ajustes estão no plano do 4933 (estado não mapeado no timeout
  vira `timeout` sem lançar; edge case do PENDING com devolução na wallet; medição na sandbox). Título
  do plano da 4934 com `{F}`. Custo até aqui: $3.72 + $7.43 + $5.12 = $16.27.
- Furo do gate 1 (origem **nosso**): o plano do 4933 trava a transação durante a chamada do refund
  (seção Concurrency). Nenhum outro provedor faz isso, nem o depósito da Paytech. Não estava entre as
  7 perguntas; aprovamos junto com "tudo como recomendado" sem ninguém decidir, e a seção Decisions
  do plano diz "None". Eu avaliei as perguntas e não li o desenho procurando escolhas não perguntadas.
  Lição para o gate 1: ler Architecture & Design atrás de escolha sem precedente no código, além das
  perguntas.
- Desfecho da trava: decisão do Lucas, seguir o PaymentIQ e tirar. Plano emendado no PR
  (`068565f06`, só o arquivo do plano). A execução aproveitou e preencheu Decisions com as 7 decisões
  do gate, cada uma com motivo e "Lucas Franco, 2026-11-12": a seção que estava "None" agora registra
  o que foi decidido.

### 4 `/sdd-implement CLS-4932` (constants) — gate 2

- Saída: commit local `429050e0`, 2 arquivos, 11 linhas: a entrada Paytech → `CARD_PAYMENT_METHODS` e
  o teste que fixa a lista e exclui applepay, googlepay, oct. Step 1: 6/6 e 130/130, em 11 s.
- Conferido: diff igual ao plano, nada fora dele; sem atribuição na mensagem; autor com o mesmo
  e-mail dos commits anteriores do Lucas.
- Erros: nenhum. Push liberado.
- Revisores, rodada 1: 7 sem achado; tests achou um furo real (o teste não cobria o caminho
  `PROVIDER_NAMES_AUTOMATIC_REFUND`, que liberaria todos os métodos). Corrigido em `2ef8db07`, uma
  asserção. Rodada 2: 8 sem achado, PR com `sdd-reviewed`. Nenhum de nós tinha visto: a revisão
  automática pagou o próprio custo aqui.
- `sdd-release`: PR de biblioteca fica fora do manifesto (o lead faz o merge e anuncia a tag quando
  a story for aceita; o payment troca o pin pela tag). Sem ação manual agora. O Lucas apontou que a
  troca do pin precisa estar escrita para quem faz o deploy: vira ação manual no release do 4933.
- Desfecho: 4932 fechado. Implement $5.95; total do ticket $9.67. Avaliação no PR "I'd merge this".
  Manifesto não criado (nada a registrar). O ajuste do plano do 4933 ($0.37) ficou sem comentário de
  custo; vai somado no comentário do implement do 4933.

### 5 `/sdd-implement CLS-4933` (payment) — 2026-11-12

- Ambiente: `make init` falhou (imagem `payment:latest-dev` de 3 meses, PHP 8.4.16 no container, master
  pede ≥ 8.5.11). `make build` reconstruiu (8.5.12) e `make init` passou. A execução separou bem o PHP
  do host do PHP do container. Confirma a linha "`make init` antes do implement" da tabela.
- Erro do plano (origem **fase**): a tarefa 7 cria as vendas Paytech com ids 6 e 7 no `setUp` do
  `RefundControllerTest`, mas `testPostRefundRejectsAlreadyRefundedTransaction` insere 6, 7 e 8 no
  mesmo arquivo (conferido no `origin/master`, linhas 163-166). Pego pelo implement antes de escrever
  código, com emenda proposta (9 e 10). O gate 1 não pegaria: exigia ler o arquivo de teste inteiro.
- Código: commit local `aa11064a9` (5 arquivos), testes do plano verdes de primeira, suite inteira e lint
  verdes; sem atribuição. Ainda sem push.
- Parada no Proteus (origem **repo**): as regras do `celesta-qaa-proteus` pedem OAS e SQL do serviço
  antes da primeira edição, id do Qase vindo da primeira execução e `.env` local; nada disso existia na
  máquina. O agente já tinha editado o helper antes de ler as regras e parou ao percebê-las. Opções: A
  (escrever sem rodar, CI do proteus valida) ou B (tirar o Proteus da rodada). Os 2 cenários do plano não
  dependem do mock da Paytech (400 de validação e webhook assinado), então A é viável. Recomendado A, sem
  pedir ao Lucas para "confirmar" OAS e SQL gerados: a fonte é o `make openapi` e o schema da stack de pé.
  Decisão do Lucas: não rodamos Proteus local; testes na branch de mesmo nome, o CI valida.
- Gate 2 (pedido de push dos dois repos): diff do payment = plano (6 arquivos, tarefas 1-4 conferidas no
  código), sem atribuição nos dois repos, merge limpo com o master atual (que andou com o CLS-2962). Os 2
  erros da suite são a colisão `DdTrace`. Proteus: 8 passos, unit 280/280; os 2 cenários já passam no
  master, então cobrem o fluxo, não a mudança (a chamada à Paytech não tem mock; fica no PHPUnit, como o
  plano dizia). Liberado.
- Review r1: 6 de 8 limpos. tests: 6 should-fix de teste, todos dentro do plano, corrigidos pelo implement
  (parcial, estado não mapeado, refund final no timeout, id consultado, assert inútil, mock estático).
  quality: duplicação entre `processRefundResponse` e `processPaymentResponse`, fora do plano (mexe no
  depósito em prod). Recomendado: recusar na thread por escopo, sem prometer follow-up que ninguém abre.
- Proteus PR #807: o hook `pre-push` não rodou o `qaa-reviewer` (sem `claude` no PATH do shell do agente) e
  o push passou sem ele. Origem **repo/ambiente**: hook que falha aberto. Pedido: rodar o hook à mão com o
  binário no PATH.
- Review r2 do payment: 8/8 limpos, `sdd-reviewed`. r1 levou 27 min, r2 87 s.
- `qaa-reviewer` (rodado à mão): 0 blocking, 4 should-fix, 3 nits. Três should-fix de tipagem e declaração
  são reais (cast inline em vez de `PaytechOptions`, resposta `Record<string, unknown>`, `const` local em
  vez de `let` declarado). O quarto pede rodar a suite local, o que contradiz a decisão do Lucas; o job
  `proteus` do CI do payment roda e dá o log. Recomendado: corrigir os 3 e os nits do enum e do generic,
  recusar o local.
- Board: o SDD não move status. Regra do Lucas: Implemented só depois do review humano. Antes de To review,
  um review nosso por agente sem contexto.
- Review sem contexto do 4932 (constants #632): limpo. Achou fora do PR: o pin do payment
  `dev-CLS-4932 as 1.366` ficou errado porque 1.366 e 1.367 foram tagueadas hoje às 14:00 (CLS-4032), depois
  do pin. Origem **nosso/fase**: alias escolhido como "próxima versão" num momento, e a lib andou. Alias
  certo agora: 1.368. Nits: Decisions "None." no plano; teste que compara a constante com ela mesma. O CI do
  constants só roda com review APPROVED ou push no master, então os testes ainda não rodaram no CI.
  4932 → To review.
- `qaa-reviewer`: 3 passadas até "No findings" (#807 em `77fc7d4d4`). CI do payment disparado à mão:
  phpunit, codestyle, openapi-lint e migration verdes; proteus 403/404. A falha é o passo `(OpenAPI)` do
  webhook: `POST /webhook/paytech` nunca foi documentado no OAS do payment (xCoins tem rota própria). Origem
  **repo**: lacuna antiga que nenhum teste exercitava; o teste novo a expôs. Recomendado: emenda que documenta
  a rota, espelhando xCoins (só atributo OA e schema, sem comportamento).
- Pin trocado para 1.368 (`f263c0b48` + emenda `fb1cf1f13`). Release `releases/CLS-4779.yaml` escrito: grupo 1
  manual, grupo 2 o #1431; 4934 fora até ter código. Ponto: o texto fixa "tag 1.368"; se outro PR do
  constants taguear antes, a tag muda. Pedido de redação: "a tag que o merge gerar (1.368 se nada entrar
  antes)".
- Fim do implement do 4933: OAS do webhook documentado por emenda; r3 achou `fraud` faltando no enum,
  r4 limpa. CI final verde (proteus 404/404; `pcp-1` My.Tu intermitente). Custo $38.70 implement, $46.50
  ticket. O relatório diz "pronto para merge" e o comentário de veredito no PR diz "I'd merge this": é o
  formato do skill, não uma ação. Nada foi aprovado nem mergeado (PR `REVIEW_REQUIRED`). Na nossa regra o
  fim do SDD leva a review sem contexto e depois To review; merge é do time dono.
- Review sem contexto do 4933: limpo. Nits: `composer.lock` gerado com Composer mais velho (plugin-api 2.9.0),
  e CANCELLED sem campos de erro gravado como "Invalid response structure" (previsto no plano). Lembrete: a
  branch do constants está 9 commits atrás do master e precisa de merge do master antes da tag. 4933 → To
  review.
- 4934 (front), sessão própria: plano sem perguntas, 3 arquivos + plano, testes 9842 verdes rodados num
  `node:24` descartável porque a imagem dev do front tem o código embutido. A mensagem de regras fixas não
  foi colada antes; parou no pedido de push. Gate 2 conferido: diff = plano, sem atribuição.
  Review r1: 8/8 limpos. Sem Proteus para o front. Release: discutimos grupo próprio x mesmo grupo; a doc
  ("grupo de PR = uma implantação automática") e os manifestos existentes (serviço e consumidor no mesmo
  grupo: CLS-3094, 3595, 4856) dão o mesmo grupo. Erro meu (origem **nosso**): recomendei grupo próprio sem
  olhar a prática. Custo $5.33 implement, $10.45 ticket. Veredito no PR já sem "pronto pra merge".
  Review sem contexto: limpo, CI verde (jest incluído). Nit: o corpo do PR ainda descreve só o plano (o
  `sdd-implement` não reescreve o corpo que o `sdd-plan` abriu). Board: esqueci de passar o 4934 de Planned
  para In Progress quando o implement começou (origem **nosso**). 4934 → To review. Os três da story em To
  review em 2026-11-12.

### 6 Review da story inteira (agente sem contexto) — 2026-11-12

Nada bloqueante. Achados que nenhum review por PR pegou, porque atravessam as peças:
- Dinheiro (origem **fase**, plano tarefa 5): resposta com `result.id` e sem `state` vira `failure` e devolve o
  saldo, mas a Paytech já criou o refund; o webhook COMPLETED depois é ignorado. Contradiz a Decision do
  próprio plano (estado desconhecido → pending). Baixa chance.
- Ordem (origem **fase**): o plano e a spec do proteus #807 dizem que não há ordem de merge; há, o passo do
  OpenAPI depende do #1431. O manifesto não tem o #807.
- Documentos (origem **fase**): o corpo dos 3 PRs ainda descreve o plano; o `sdd-implement` não reescreve.
- Eventos em dobro quando webhook e resposta direta chegam juntos (sem trava, como PaymentIQ): wallet
  segura; o segment não foi conferido. Padrão dos outros provedores, não corrigir.
- Leitura: o review por PR (8 revisores + o nosso) não vê contrato entre repositórios nem ordem de deploy.
  O review da story inteira é um passo que o SDD não tem.
- O pai ganhou A-Team **e F-Team** em components, sem ter sido a execução: o F-Team foi o Pedro, 2026-11-12
  10:59, 20 min depois do split. Mudança do PO, não erro; fica como está.
- Lições desta rodada levadas para o procedimento: overlay ("Bibliotecas compartilhadas", release) e
  `ticket-story.md` ("O que conferir em cada parada do SDD").
- 4934: o agente achou sozinho o endpoint de constantes do BO e pesou ler de lá contra manter a lista;
  recomendou manter (ler exigiria bump do constants no backoffice, 4ª sub-task).
- Erro (origem **fase**): o rascunho da 4934 pôs `{A}` no título do plano, divergente do Jira (`{F}`).
- Respostas: todas como recomendado; título do plano igual ao Jira.
- Leitura: as perguntas do `sdd-plan` foram de engenharia de verdade, com evidência e recomendação.
  Nesta fase o formato só SDD está entregando sem correção nossa de conteúdo.
- Leitura: o split achou sozinho as duas listas de allowlist e o front hardcoded, que é o que um split feito de memória esqueceria. A pergunta "crio?" é o gate natural; não houve pergunta de negócio.

---

## CLS-1214 — combinar saques num payout

### 7 Plan: draft de todas as sub-tasks, pelo Celly Dev — 2026-11-13, gate 1

- Saída: rascunhos de 4753 (payment), 4754 (statistics), 4755 (wallet), 4756 (backoffice), 4757 (front) em
  `/tmp/cls1214/drafts/`, cada um com um arquivo de contrato para o próximo. Nada escrito no git nem no Jira.
  A sessão encadeou sozinha: 4753 → 4754 ∥ 4755 → 4756 → 4757, passando o contrato do rascunho anterior.
- 4758 (cleanup) morreu três vezes com 403 da Cloudflare. Adiado: só sai depois do 4757 em produção, então
  o plano lê o código final (Lucas).
- Erros:
  - ~~4754: migration `Version20261408000001` com mês 14 (fase).~~ Erro meu, não da fase: o master da
    statistics já vai até `Version20261407000004`, então o rascunho seguia a sequência do repositório. Pedi
    para renomear para `20261113…` e a execução apontou o problema; a correção volta para `20261408000001`.
  - 4753 e 4755: limite de 10 ids numa constante de biblioteca que não existe, pedindo re-split e pin
    (fase: recomendação sem prova de necessidade; nenhum limite da Genome ou My.Tu no código).
  - 4756 Q3: mock e proteus em dois repositórios a mais para um campo repassado com `?? null` (fase).
  - 4756 diz que `withdrawRequestId` cobre o rollback até o 4758; com o 4757 sem fallback, não cobre (fase,
    pego pelo próprio rascunho do 4757).
- Acertos: cada plano marcou escolha sem precedente; a ordem de deploy payment → statistics → wallet saiu
  dos próprios rascunhos; nada do nosso fluxo no texto.
- Processo (Celly): a execução leu ticket-story e os arquivos do sprint porque o prompt citava "gate 1";
  escreveu no nosso `sdd.md`; rascunhos em `/tmp`; cinco quedas por 403 em subagentes paralelos.
  Prompt de correção mandado à conversa que constrói o Celly.
- Leitura: rascunho de todas as sub-tasks de uma vez, com contrato passado por arquivo, deixou o gate 1 da
  story inteira numa leitura só, que era a decisão de 11/11.

### 7 Plan: respostas do gate 1 aplicadas — 2026-11-13

- Sessão travou 30 min num pedido de permissão (cópia com `>`) que o chat do Celly não mostrava. Destravou
  com a instrução de editar no lugar, com Edit.
- Respostas aplicadas nos cinco rascunhos. O corpo dos planos (dentro do bloco) não cita o nosso fluxo; "Gate 1"
  e `/tmp` aparecem só no cabeçalho do rascunho, fora do plano.
- A execução levantou dois pontos, os dois conferidos no `origin/master`:
  - payment `additional_data_value` é `VARCHAR(512)` (`TransactionAdditionalData.php:34`), cerca de 60 ids.
    A transação é salva antes do `doPayout` (`PayoutController.php:592–596`): lista longa falha antes de
    pagar, nada sai. Edge case sem validação está certo.
  - migration da statistics: ver a correção acima.

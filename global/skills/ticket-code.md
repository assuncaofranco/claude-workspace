---
description: Write the fix or feature for a ticket, after ticket-understand and ticket-test have run. Applies the project's coding constraints at generation time, not after the fact.
argument-hint: <TICKET>
---

# ticket-code

Write the code for `$ARGUMENTS`. Assumes `ticket-understand` already produced the business-logic
understanding and `ticket-test` already produced or updated the scenario used to drive and verify it.
Do not start this step from a bare ticket description alone.

Project-specific constraints — forbidden functions, lint thresholds, which shared library owns what,
and the known test backlogs — live in the project's own standards file and context table (for
Celesta: `celesta-microservices/shared/coding-standards.md` and
`celesta-microservices/constants-backlog.md`).

## Regras — aplicar enquanto escreve, não esperar o review pegar

**As células A da matriz são o escopo, todas elas.** Toda célula que o `ticket-matrix` marcou como
afetada é requisito, não caso de borda. Célula A sem caminho de código é ticket inacabado, e
"funciona para o tipo principal" é exatamente a implementação parcial que faz ticket voltar
rejeitado. Se, escrevendo, uma célula exigir algo que o plano não previu, **dizer** — em vez de
implementar em silêncio o subconjunto que era fácil.

**Nunca tocar linha que não precisa.** Mudar só o que o ticket exige. Não rodar formatador de arquivo
inteiro (`php-cs-fixer`, `csfix`, o "reformat file" da IDE) num arquivo só porque você editou duas
linhas nele: isso reescreve estilo pré-existente não relacionado — alinhamento de parâmetro,
visibilidade faltando, vírgula final, linha em branco — e transforma um diff de 3 linhas num de 40,
o que torna a mudança real mais difícil de revisar. É exatamente o tipo de limpeza não pedida que não
se quer aqui.

Se o linter apontar problema de estilo pré-existente num arquivo que você tocou, **deixar** — a menos
que ele faça o arquivo estourar os thresholds configurados de verdade. Algumas linhas apontadas com a
nota agregada confortavelmente acima do limite não é motivo para reformatar o arquivo.

**Funções proibidas, armadilhas de lint, thresholds.** Estão no arquivo de padrões do projeto. Ler
antes de escrever, não deduzir de memória — ele é a fonte única, e não se duplica o conteúdo aqui.
Ele também tem uma seção de **lições de review**: erros que um humano ou um revisor automático já
pegaram antes. Consultar, e depois de qualquer rodada de review que pegue algo novo, acrescentar o
item lá para não repetir.

**Dependência de biblioteca compartilhada no composer.** Se o ticket depende de mudança numa
biblioteca compartilhada, verificar que o `composer.json` do serviço já aponta para `dev-<TICKET>`
**antes** de escrever código contra ela — nunca uma versão estável durante o desenvolvimento. O
composer só sobe para uma tag estável depois do aceite de QA/PO. Se ainda não aponta para a branch de
desenvolvimento, sinalizar e corrigir isso primeiro.

Nota: `dev-<branch>` no composer, não repositório `path` local — o `path` funciona na sua máquina e
quebra em qualquer outro lugar.

**Nome de arquivo de migration.** Nunca escrever à mão o nome/classe `Version<timestamp>`. Gerar com
o comando de geração do framework e preencher o `up()`/`down()` do stub. Timestamp escolhido à mão —
sobretudo um com muitos zeros à direita — colide com facilidade e parece fabricado no review.

**Corrigir migration no meio do ticket.** Se um defeito na migration aparece durante o teste (uma
coluna faltando, por exemplo) e **nada desta branch foi implantado em ambiente real ou compartilhado
ainda**, editar a migration existente no lugar — reverter local, editar, reaplicar — em vez de
empilhar uma nova. Só criar migration nova quando algo anterior já está implantado em algum lugar
real; é isso, e só isso, que torna a migration "histórico imutável".

## Constantes e jobs — nunca definir localmente

Não criar constante dentro de um serviço nem classe de job de messenger dentro de um serviço: as duas
coisas pertencem a bibliotecas compartilhadas. Se o ticket precisa de uma das duas, **parar e avisar**
que tem que ser adicionada à biblioteca primeiro, na branch de desenvolvimento dela.

Adicionar constante costuma quebrar um teste em outro serviço — o que publica a lista de constantes.
Esse é o único lugar onde "não mudar o que o ticket não precisa" **não** vale: o teste afirma o
payload inteiro, então ele não passa só com as suas chaves adicionadas. Reconciliar tudo, e avisar o
usuário quando a parte herdada for grande — um ticket de duas constantes com sessenta linhas de diff
no teste precisa dessa explicação, e o tamanho é um fato sobre a dívida acumulada, não sobre a sua
mudança. O detalhe de qual teste e por quê está no arquivo do projeto.

## Próximo

Entregar para `ticket-review`.

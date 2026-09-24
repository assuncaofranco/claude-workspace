# Lente de review

De onde tirar a verdade, e como pesar um achado. Carregado no passo 13.

## A verdade vem do git, não da conversa

Ao revisar um diff, re-derivar tudo de `git status` e `git diff` contra o estado real da branch —
**mesmo que a mesma conversa já tenha planejado e discutido cada mudança em detalhe**.

**Por quê:** dito explicitamente durante o review de CLS-1285-CLS-2391 — *"vc é só o reviewer, não
quero que use memória pra fazer review"*. A implementação diverge do que foi planejado, e essa
divergência é exatamente o que um review existe para pegar. Pego assim naquela sessão: um
`composer.json` apontando para um repositório `path` local não ignorado pelo git, que nenhum plano nem
descrição mencionava.

**Como aplicar:** para cada repositório tocado, rodar `git status` / `git diff master` do zero antes
de comentar. Não resumir do que foi dito antes sobre "o que a correção faz".

## "É inócuo hoje" não basta para descartar

Ao decidir aceitar ou descartar um comentário de review — de um humano ou de um revisor automático —
"não tem efeito dado o código atual" **não** é motivo suficiente. Verificar se a preocupação se torna
real sob uma mudança plausível e próxima, e pesar o impacto de produto daquele cenário.

**Por quê:** pego no CLS-1285-CLS-2391. O revisor apontou que um setter podia sobrescrever com `null`
um valor já definido, já que o campo do job é nullable. Primeira leitura: descartado como inócuo,
porque nada mais no código escreve aquele campo hoje. O Lucas empurrou de volta — o próprio texto do
ticket já indicava que o campo passaria a ser populado em outras transições. A pergunta real é o que
acontece quando isso entrar, não se o diff de hoje é seguro isolado. Reformulada assim, a guarda é
barata e é seguro contra perda silenciosa de dado (replay de fila antigo apagando valor que a própria
aplicação tinha definido) — vale aplicar mesmo sem mudar nada do comportamento atual.

## Citar a fonte canônica, não "o padrão"

Quando um achado invoca uma regra de estilo ou de função proibida, nomear a **fonte real** — o arquivo
e a classe que definem a regra — não "o coding standard".

**Por quê:** pedido explicitamente durante um review de PR de outra pessoa, depois de um achado sobre
função proibida: ele queria o achado rastreável, não afirmado. E depois esclareceu que a citação deve
ser o caminho canônico da biblioteca, não a cópia em cache nem a de `vendor/` de um serviço — essa
está presa à versão que o lock resolveu e pode estar atrás do repositório.

O caminho canônico do projeto fica no overlay dele. O cache local serve para consulta rápida; a
citação no comentário é sempre a fonte.

## Ordem

Intenção antes de código; matriz antes de qualidade. Um achado de qualidade num caminho que a matriz
nem classificou é ruído — e a classificação pode revelar que o achado nem é alcançável.

Lição que o review produziu volta para o corpo de regras, via `corpus.md`. Review que não realimenta
nada repete o mesmo achado no ticket seguinte.

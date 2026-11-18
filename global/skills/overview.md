---
description: Show Lucas the basics of what a ticket changes — endpoints, entities, commands and jobs — from the delivered code or, failing that, the plan, so he can decide and ask without reading code. Pass a parent key (all its sub-tasks) or a sub-task key.
argument-hint: <PARENT or SUB-TASK key>
---

# overview

Passo de leitura, não de revisão: mostra **o que muda para quem está do lado de fora** de cada
sub-task de `$ARGUMENTS`, para o Lucas decidir e perguntar sobre o que importa sem abrir código. A parte
interna (classes, camadas, refatoração, decisões menores, a lista de decisões) não entra.

Somente leitura. Nada de commit, push, comentário no Jira, arquivo gravado, `checkout` no clone, nem
subir ou derrubar stack: há uma stack por serviço na máquina e o checkout montado nela pode ser de outra sessão. Tudo sai
de `git show`/`git archive` do ref e de container descartável.

Constantes (campo do repositório, site do Jira, raiz dos clones, caminho dos scripts) vêm do projeto
(Celesta: `celesta-microservices/context.yaml`, `sdd:` e `meta:`).

## 1. Sub-tasks

- Chave de **pai**: todas as sub-tasks (`parent = <KEY>` no Jira, campos: resumo, status, repositório).
- Chave de **sub-task**: só ela.

## 2. Fonte, por sub-task, o que existir no momento

Repositório = campo de repositório da sub-task; clone = `<raiz>/<repositório>`. `git fetch origin` no
clone antes de ler (fetch, nunca pull nem checkout).

1. **Ref.** `origin/<KEY>`; se a branch local `<KEY>` existir e tiver commits que o origin não tem,
   usar a local e dizer "inclui commits ainda não enviados". Sem nenhuma das duas: "sem branch, sem
   plano" e a sub-task fica numa linha.
2. **Tem código?** `git diff --name-only <base>...<ref> -- . ':(exclude).sdd'` não vazio (`<base>` =
   `origin/master`, ou a branch padrão do repositório). Se sim, a fonte é **o código entregue**. Se
   não, e existe `.sdd/_plans/<KEY>.md` no ref, a fonte é **o plano**. Cada sub-task diz no cabeçalho
   qual das duas, e para o código o ref e o commit.

Plano de uma sub-task que já tem código não é fonte: o código manda, o plano só serve para achar onde
olhar.

3. **Base empilhada.** Sub-task bloqueada por outra no mesmo repositório costuma nascer da branch dela
   (ou fazer merge dela), e aí `origin/master...<ref>` traz o trabalho das duas. Conferir os assuntos de
   `git log <base>..<ref>`: chave de outra sub-task cuja branch é ancestral do ref → `<base>` passa a ser
   a ponta dessa branch, e o cabeçalho diz "empilhada sobre <OUTRA-KEY>". Sem isto a sub-task é
   creditada com endpoint, migration e command que não são dela.

## 3. Endpoints (fonte: código)

1. **Gerar e comparar o OpenAPI.** Nenhum serviço versiona o arquivo, então os dois lados são gerados
   agora, nunca o `public/open-api.json` que estiver no disco:
   ```bash
   scripts/openapi-ref.sh <serviço> <base>  <tmp>/base.json
   scripts/openapi-ref.sh <serviço> <ref>   <tmp>/branch.json
   python3 -I scripts/openapi-diff.py <tmp>/base.json <tmp>/branch.json
   ```
   `<serviço>` é o nome completo (`celesta-backoffice`): o sufixo é ambíguo com o front. O gerador usa
   `vendor/` do clone principal, então um clone com dependências velhas falha com "class not found"
   (aconteceu no scenario): é o caso de "gerador que falha" abaixo, não de consertar o clone.
   O diff lista cada operação criada, removida ou alterada, campo a campo. Serviço sem gerador (saída 3:
   Go, front, etl) ou gerador que falha: **dizer isso na sub-task** e tirar o contorno do diff do código
   (rotas, atributos de schema, chamadas HTTP novas), marcado "sem OpenAPI". Nunca inventar campo.
2. **O OpenAPI não cobre tudo.** Erro novo, validação nova e campo que mudou de significado muitas vezes
   não mexem na anotação. Ler no diff do código onde a operação passa a recusar algo, e pegar a
   **mensagem literal** (a regra de negócio mora aí). Erro que está no código e não no OpenAPI entra,
   marcado "não documentado".
3. **Compatibilidade, uma linha por endpoint.** Quebra quem chama hoje: campo obrigatório novo no
   request, campo removido ou renomeado na resposta, tipo ou enum mais estreito, status ou rota
   removidos, erro novo para entrada que antes passava. Não quebra: campo opcional novo no request,
   campo novo na resposta, rota nova. Dizer **quem chama hoje** (grep do caminho nos outros clones, em
   `origin/master`) e, quando o chamador é outra sub-task da mesma story, qual.

## 4. Entidades (fonte: código)

Migration do ref, contra a mesma `<base>` (`migrations/` ou o equivalente do serviço), lida do arquivo, não da entidade. Por
tabela: campos novos, alterados e removidos com tipo, nullable e default; índice e chave estrangeira em
uma linha cada. Só isso. Mapeamento de entidade sem migration correspondente, ou o contrário: **dizer**,
é divergência.

## 5. Command, job ou script (sem exposição)

Qualquer coisa nova ou alterada que roda sem requisição: command, handler de job, cron, script de
migração de dados. Por item, nesta ordem: **o que dispara** (cron e frequência, fila, manual), **tamanho
do lote**, **memória**, **tempo**, **lock**, **idempotente ou não** e **o que acontece se parar no
meio**.

**Todo número vem com a conta que o justifica**, no mesmo formato do exemplo: "lote de 1000 porque
1000 × ~78 KB por linha ≈ 78 MB, abaixo dos 128 MB do container". As entradas da conta saem de onde
existirem: o lote, do código; o tamanho da linha e o número de linhas, do banco em leitura
(`skills/db-query.md`, `information_schema` e contagem); o limite do container, do manifesto de deploy.
Entrada que não se acha vira "não medido: falta X", **nunca** um número sem conta. O tempo estimado
também leva a conta (linhas ÷ vazão observada ou declarada).

## 6. Fonte: plano

Tudo acima, mas lido do plano e **marcado "plano, ainda sem código"**: endpoint, request, response e
erros como o plano os descreve; tabela e campos da seção de arquitetura. Sem OpenAPI para gerar, então
a compatibilidade é do que o plano diz; se o plano é vago num ponto (erro sem mensagem, lote sem
número), a linha diz "o plano não define" em vez de preencher.

## 7. Saída: o chat, não um arquivo

O resultado **é a resposta no chat**: os endpoints, entidades e commands, no formato abaixo. **Não
gravar arquivo** (nem `tickets/<KEY>/overview.md`, nem outro). O Lucas lê aqui e pergunta aqui; um
arquivo que ele precisa abrir é um passo a mais que o `/overview` existe para evitar.

**Por quê:** correção do Lucas, 2026-11-17 (CLS-3916): a skill gravava `overview.md` na pasta do ticket
e respondia no chat só uma linha por sub-task e o caminho. Ele queria o conteúdo no chat.

Português, terse (`rules/writing.md`): o conteúdo do overview é a própria entrega, então ele vai inteiro
no chat; o que continua fora é comentário, recomendação e resumo de cortesia.

````markdown
# <KEY> — overview
<data> · <N> sub-tasks

## <SUB-KEY> · <repositório> · <resumo>
**Fonte:** código (`<ref>` @ `<commit curto>`)  |  plano (`.sdd/_plans/<SUB-KEY>.md`, sem código ainda)

### <criação|alteração|remoção> · <MÉTODO> <URL>
**Request**
```json
{
  "campoNovo": 12,            // + integer|null, opcional
  "campoRemovido": "x",       // − string
  "campoAlterado": "abc",     // ~ string → string|null
  "…": "o resto não mudou"
}
```
**Response 200** (mesmo formato)
**Erros novos**
- 400 `<mensagem literal>` — <quando>
**Compatibilidade:** <uma linha: quebra ou não, e quem chama hoje>

### Entidade · <tabela>
| Campo | Tipo | Nullable | Default | Mudança |

### Command · <nome>
Dispara: … · Lote: … (conta) · Memória: … (conta) · Tempo: … (conta) · Lock: … ·
Idempotente: … · Se parar no meio: …
````

- Só o que mudou aparece marcado; o contexto em volta se resume em `"…"`.
- Seção sem conteúdo **sai** (sub-task sem entidade não ganha "Entidade: nenhuma").
- Sub-task sem nada que atravesse a fronteira (refatoração, só teste): uma linha, "sem mudança de
  contrato".

## 8. Fecho

Depois das sub-tasks, em uma linha cada, o que limitou a leitura (sub-task sem OpenAPI, gerador que
falhou, número que ficou "não medido", sub-task sem branch). Nenhuma recomendação.

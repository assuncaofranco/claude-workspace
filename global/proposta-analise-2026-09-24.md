# Proposta — fechar o buraco na fase de análise

Rascunho para decisão. **Nada em `rules/` ou `skills/` foi editado** — `corpus.md` manda mostrar o
conflito e perguntar antes. As perguntas estão no fim.

Origem: os seis achados do review interno de CLS-2973, em 2026-09-24.

---

## 1. O diagnóstico

Quatro dos seis achados nasceram num artefato, não no código. A implementação seguiu fielmente um
plano errado. Isso é bom sinal — significa que o código parou de ser onde o erro entra — e diz onde
atacar agora.

| Achado | Onde nasceu | Classe |
|---|---|---|
| Behat não testava o que o nome dizia | plano | análise |
| "No Postman collection" contradizendo o disco | plano | manutenção de artefato |
| Matriz nunca saiu do chat | transição matriz → spec | mecânica |
| "nada em runtime lê currency" (falso) | spec | **análise** |
| Docblock com id de ticket no fonte | implementação | regras não lidas |
| Diff ruidoso por reescrita | implementação | técnica |

Mas contar achados subestima o custo. O erro de análise mais caro do ticket **não** está nessa
lista, porque o review não o pegou — ele apareceu como rodadas de conversa desperdiçadas:

- afirmei que nada em runtime olha moeda, e existia um validador de moeda no engajamento;
- levantei dois "achados" que eram de outros times (front do BO, portão 40), e fui corrigido duas
  vezes;
- não separei *momento de configuração* de *momento de runtime* até o Lucas forçar, o que produziu a
  pergunta "de que vale essa implementação, se o player não vai receber nada?".

Os três têm a mesma causa.

## 2. A causa: o ticket é sobre um conceito, e a análise mapeia um objeto

O ticket era sobre **moeda**. Eu mapeei **segmento** — grepei os consumidores de `SegmentService`,
confirmei que só um lia `currency`, e concluí. A conclusão estava certa sobre segmento e errada
sobre moeda, porque moeda decide coisas em pontos do sistema que não tocam segmento nenhum.

`ticket-matrix` não pega isso, e não deveria: ela enumera as **entradas** de um trecho de código que
já foi escolhido. As oito células de CLS-2973 estavam corretas. O erro foi antes — na escolha de
qual trecho olhar.

Falta um artefato entre o passo 2 (ler o código do domínio) e o passo 3 (matriz): **onde o conceito
do ticket decide alguma coisa, ao longo de todo o fluxo, e de quem é cada ponto.**

## 3. O artefato proposto — mapa de decisão

Uma tabela, produzida no passo 2, antes da matriz. Para CLS-2973 teria ficado assim:

| # | Momento | O que decide | Onde | Dono | No escopo? |
|---|---|---|---|---|---|
| 1 | CRM monta a config no BO | dropdown lista só segmentos da moeda da config | `bonusModel.js:547` (front) | front | não |
| 2 | CRM salva a config | `segmento.currency` vs `config.currency` | `SegmentConstraintValidator:81` | D | **sim — é o ticket** |
| 3 | Segment avalia o jogador | só avalia segmentos da moeda do jogador | `SegmentRepository:88` | C | não |
| 4 | Jogador engaja | `player.currency` vs `config.currency` | `PlayerCurrencyMatchValidator:35` | D | não — outro ticket |
| 5 | Bônus é creditado | moeda da carteira | wallet | — | não |

Cinco linhas. Com ela em mãos no começo:

- a frase "nada em runtime lê currency" não teria sido escrita — a linha 4 a contradiz;
- eu não teria levantado as linhas 1 e 3 como achados, porque a coluna Dono já diz que não são
  nossas;
- a pergunta "de que vale, se o player não recebe" se responde apontando para as linhas 2 e 4,
  em vez de três rodadas de conversa.

**Como se produz.** Uma busca dirigida pelo substantivo do ticket — aqui, `currency` — nos pontos de
decisão de cada serviço que o fluxo atravessa, não em todo o código. Condições, validadores,
cláusulas de filtro. É meia dúzia de greps, não um levantamento arquitetural.

**Quando não se faz.** Ticket cujo conceito vive num lugar só e isso é evidente da leitura do passo
2. A tabela de uma linha não informa nada — ela existe para quando o conceito se espalha.

## 4. As três regras que os achados pedem

### 4.1 Afirmação negativa carrega a busca que a sustenta

Quando um artefato afirma que algo **não** acontece — "nada lê X", "nenhum caminho faz Y", "não há
outro consumidor" — a frase traz junto o comando ou o `arquivo:linha` que sustenta.

**Por quê:** afirmação positiva errada quebra um teste. Afirmação negativa errada não quebra nada e
sobrevive no artefato — a spec de CLS-2973 teria carregado "never look at currency" indefinidamente.
E o custo de cumprir é o que teria evitado o erro: para citar a evidência, eu teria que rodar o grep
por moeda, e o validador teria aparecido na hora de escrever, não no review.

### 4.2 Plano declara a asserção, não o arquivo

Para cada teste que o plano manda criar ou alterar: a asserção e o **valor do fixture que a torna
válida**.

**Por quê:** o plano de CLS-2973 dizia "inverter o cenário, agora declarado sem a coluna currency".
A implementação obedeceu, e o cenário passou a provar ausência da chave em vez de divergência do
valor — com o nome prometendo a segunda. Se o plano tivesse escrito "segmento EUR contra config CAD,
esperando 200", o erro não teria como acontecer.

### 4.3 Passe adversarial no plano, antes de implementar

O mesmo tipo de leitura que se faz no código depois, feita no plano antes. Duas perguntas por item:
*isto prova o que diz provar?* e *isto ainda descreve o que está no disco?*

**Por quê:** pega a classe inteira de erro de artefato quando ela custa uma edição de markdown, e não
depois de código escrito, testado e revisado. Os dois achados de plano do CLS-2973 caem aqui.

## 5. O conflito que isto cria — decisão do Lucas

`skills/ticket-understand.md`, passo 2:

> Explore only the domain classes the ticket actually names or implies plus their direct
> collaborators — a full architectural survey of the service wastes tokens on
> controllers/forms/normalizers that have no bearing on this ticket.

O mapa de decisão pede o contrário: olhar pontos que o ticket **não** nomeia, em serviços que ele
não toca. A linha 4 da tabela está num validador que CLS-2973 não menciona, e é a linha que teria
evitado o erro.

Pelo `corpus.md`, isto é para ser mostrado, não contornado. As duas saídas:

- **Exceção nomeada**, dentro do próprio `ticket-understand.md`: a regra geral continua valendo, com
  a exceção de uma busca dirigida por um conceito — um substantivo só, nos pontos de decisão. O que
  a regra original proíbe é o levantamento largo; isto é estreito e barato.
- **Substituir**: a regra foi escrita contra desperdício de token, e o desperdício de rodada de
  conversa saiu mais caro neste ticket que o de token.

Minha recomendação: exceção nomeada. A regra original está certa no caso comum — a maior parte dos
tickets não tem conceito espalhado, e o levantamento largo continua sendo desperdício.

## 6. Onde cada peça entraria

| Peça | Arquivo | Por quê |
|---|---|---|
| Mapa de decisão | `skills/ticket-understand.md`, passo 2 | é sequência de passos de um fluxo |
| Afirmação negativa (4.1) | **indefinido** | é regra de como trabalhar, vale em qualquer empresa — mas não cabe em `writing.md` (voz) nem em `review-lens.md` (só review). Ver pergunta 3 |
| Plano declara asserção (4.2) | `skills/ticket-code.md` ou o passo 4 do router | fica onde o plano é escrito |
| Passe adversarial no plano (4.3) | `router.md`, passo novo entre 4 e 5 | é ordem de fluxo |
| Lições do review de CLS-2973 | `celesta-microservices/shared/coding-standards.md` e `global/shared/engineering-discipline.md` | já pendentes do review |

## 7. O que eu não proponho

- **Checklist antes do commit.** O que falhou não foi disciplina na saída, foi a análise na entrada.
  Checklist no fim pega erro de forma; nenhum dos quatro achados de artefato é de forma.
- **Mais fases no fluxo.** Já são quinze passos. O mapa de decisão entra dentro de um passo que já
  existe, e o passe adversarial é uma leitura, não uma fase.
- **Matriz mais detalhada.** A matriz de CLS-2973 estava certa. O problema era anterior a ela.

---

## Perguntas

1. **Mapa de decisão entra?** Se sim, dentro de `ticket-understand` passo 2, ou skill própria entre
   os passos 2 e 3?
2. **Conflito da seção 5:** exceção nomeada ou substituir a regra do passo 2?
3. **Onde mora 4.1** (afirmação negativa com evidência)? As opções que vejo: arquivo novo
   `rules/evidence.md`; ou dentro de `review-lens.md`, ampliando o escopo dele para além do review.
   Pelo `corpus.md`, quando não cabe em nenhuma linha da tabela, é para perguntar — é o caso.
4. **Passe adversarial no plano:** passo numerado no router, ou parte do `ticket-code`?

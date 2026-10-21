# Onde cada artefato é salvo

Carregado no passo 6 (coleção) e no 14 (deploy). O caminho concreto de cada um fica no overlay do
projeto; aqui está a regra que decide o caminho.

## Spec e plano moram onde o SDD do projeto diz, e só lá

Spec e plano não ganham cópia em arquivo — nem no repositório do serviço, nem na pasta do ticket, nem
como rascunho "para depois subir". Onde eles moram é do overlay do projeto.

**Por quê:** o SDD da Celesta passou a guardar spec e plano no Jira (2026-10-14) justamente para não
existir uma segunda cópia que diverge. Um `_specs/<ticket>.md` ao lado é exatamente essa segunda
cópia, e quem lê o arquivo lê a versão errada.

**Como aplicar:** o que for decisão vai para o artefato pela fase do SDD que é dona dele — uma
divergência descoberta no código volta para a spec ou para o plano (amend upstream), não para um
arquivo novo. `_specs/` e `_plans/` antigos num serviço são legado: servem de histórico, não de fonte.

## Coleção e matriz ficam do nosso lado, nunca num repositório de serviço

Coleção de Postman e matriz são ferramentas do nosso fluxo, não artefatos do time. Com ticket, vão
para a pasta do ticket no overlay (`matrix.md`, a coleção e o runbook). Sem ticket (reproduzir um bug
achado no meio de uma investigação), a coleção vai para a pasta local de coleções.

**Por quê:** o SDD do time (playbook `celesta-engineering-playbook`) não tem passo nem pasta de
how-to-test. A pasta `_how_to_test/` dentro do serviço era convenção do SDD antigo, criado por nós
dois, e não foi adotada pelos superiores. Uma coleção dentro do repositório entra na branch e no PR,
e aí o time lê a nossa ferramenta como se fosse dele (`writing.md`, "O nosso fluxo não aparece no
artefato do time"). Decisão do Lucas, 2026-10-20.

**Como aplicar:** sem id de ticket, usar um slug descritivo curto em vez de travar perguntando. Quando
o ticket existir, mover os arquivos para a pasta dele e renomear para o id. Os `_how_to_test/` já
commitados nos serviços são legado, como `_specs/` e `_plans/`: não se mexe, não se acrescenta.

Nesse modo ad-hoc, a regra "testar a FEATURE, não o bug" **não** vale — demonstrar o bug ponta a ponta
pode ser o objetivo inteiro.

Coleção versionada nunca carrega credencial: ver `secrets.md`.

## Épico multi-ticket se planeja fora das branches

Antes de rodar a fase de spec de qualquer ticket de um épico, montar o planejamento numa pasta própria,
fora das branches:

```
<épico>/
├── epic.md                    ordem, dependências, decisões transversais, recursos
│                              compartilhados, divergências entre a AC do épico e as
│                              subtasks, pontos abertos
├── <ticket>/notes.md          achados e rascunhos daquele ticket antes da spec —
│                              nunca cópia da descrição do Jira
└── ...
```

**Por quê:** os problemas que mais custam tempo num épico são todos *entre* tickets — a ordem de
dependência, quem implementa o que dois tickets reivindicam, e divergência entre a AC do épico e a das
subtasks. Nenhum desses cabe na branch de uma subtask, porque nenhuma delas é dona da decisão.

Spec e plano continuam no lugar que o SDD dá a eles. O que vai para a pasta do épico é o que atravessa
os tickets — o split ordena repositórios dentro de um pai, nunca pais entre si.

## Instruções de deploy ficam com o ticket e com os PRs

O arquivo completo vai para a pasta do ticket no overlay do projeto (`deployment-instructions.md`), e a
versão curta vai na descrição de cada PR envolvido. Conteúdo e método: `skills/deploy-instructions.md`.

**Por quê:** quem faz o deploy lê o PR, não a pasta do ticket. A pasta guarda o porquê, para quando
alguém precisar decidir fora da ordem ou fazer rollback.

## Memória

Memória de ticket em `memory/tasks/<ticket>/`; conhecimento durável por serviço ou domínio em
`memory/projects/<nome>/`; incidente de produção em `memory/oncall/<AAAA-MM-DD>-<serviço>.md`. A raiz
guarda só o índice.

Um arquivo, um fato, com frontmatter (`name`, `description`, `metadata.type` entre
`user`/`feedback`/`project`/`reference`). Ligar memórias relacionadas com `[[nome]]`. Data relativa
vira absoluta. Não guardar o que o repositório já registra — estrutura do código, histórico do git —
nem o que só importa àquela conversa.

Regra de **como trabalhar** não é memória: vai para `rules/`, via `corpus.md`.

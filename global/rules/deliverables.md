# Onde cada artefato é salvo

Carregado no passo 4 (spec e plano) e no 6 (coleção). O caminho concreto de cada um fica no overlay do
projeto; aqui está a regra que decide o caminho.

## Entrega não mora na pasta de ferramenta

Spec e plano de um ticket vão para a pasta de entregas do projeto, **não** para a pasta onde moram os
templates que os geram. Misturar infraestrutura com entrega faz as duas ficarem difíceis de achar.

O layout é **por serviço** — não assumir um pelo outro. Conferir no `git log` do próprio serviço antes
de criar o arquivo.

## Coleção ad-hoc fica fora de todo repositório de serviço

Coleção montada fora do fluxo formal — reproduzir um bug achado no meio de uma investigação, antes de
existir ticket — vai para a pasta local de coleções, nunca para dentro do repositório de um serviço.

**Por quê:** essas coleções não são para ser commitadas numa branch. A pasta existe justamente para
que o ad-hoc não polua repositório de serviço nem seja commitado por acidente. Ela fica fora de todo
repositório de serviço, então nada ali vaza para uma branch sem querer.

**Como aplicar:** sem id de ticket, usar um slug descritivo curto em vez de travar perguntando. Quando
um ticket de verdade for aberto para o problema, mover os dois arquivos para a pasta de how-to-test
daquele serviço e renomear para o id.

Nesse modo ad-hoc, a regra "testar a FEATURE, não o bug" **não** vale — demonstrar o bug ponta a ponta
pode ser o objetivo inteiro.

Coleção versionada nunca carrega credencial: ver `secrets.md`.

## Épico multi-ticket se planeja fora das branches

Antes de rodar o `/spec` de qualquer subtask de um épico, montar o planejamento numa pasta própria,
fora das branches:

```
<épico>/
├── epic.md                    ordem, dependências, decisões transversais, recursos
│                              compartilhados, divergências entre a AC do épico e as
│                              subtasks, pontos abertos
├── <subtask>/description.md   descrição do Jira verbatim + rascunhos daquele ticket
└── ...
```

**Por quê:** os problemas que mais custam tempo num épico são todos *entre* tickets — a ordem de
dependência, quem implementa o que dois tickets reivindicam, e divergência entre a AC do épico e a das
subtasks. Nenhum desses cabe na branch de uma subtask, porque nenhuma delas é dona da decisão.

Spec e plano continuam nascendo nas branches. O que vai para a pasta do épico é o que atravessa elas.

## Memória

Memória de ticket em `memory/tasks/<ticket>/`; conhecimento durável por serviço ou domínio em
`memory/projects/<nome>/`; incidente de produção em `memory/oncall/<AAAA-MM-DD>-<serviço>.md`. A raiz
guarda só o índice.

Um arquivo, um fato, com frontmatter (`name`, `description`, `metadata.type` entre
`user`/`feedback`/`project`/`reference`). Ligar memórias relacionadas com `[[nome]]`. Data relativa
vira absoluta. Não guardar o que o repositório já registra — estrutura do código, histórico do git —
nem o que só importa àquela conversa.

Regra de **como trabalhar** não é memória: vai para `rules/`, via `corpus.md`.

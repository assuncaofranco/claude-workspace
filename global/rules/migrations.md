# Migration que trava tabela: analisar com dado de produção antes

Carregado **sempre** que um plano, um diff ou um review contém DDL (`CREATE`, `ALTER`, `DROP`,
`RENAME`, índice, chave estrangeira). Vale no plano, na implementação, no review dos nossos tickets e
no review dos tickets dos outros. Não tem exceção por tamanho de ticket nem por expedite.

> **Nenhum DDL sobre tabela existente vai para produção sem a análise abaixo escrita no plano.**
> **Sem análise, o plano não passa e o PR não é aprovado.**

## Por quê

Em 2026-11-17 a migration do CLS-4540 (promotion v1.403) derrubou o prod-1 por 9m49s: toda leitura
de `reward_configuration` e de `bonus` morreu no limite de 25 s, e o gateway registrou cerca de 8.600
erros. A migration criava uma tabela nova e vazia, com uma chave estrangeira para
`reward_configuration`. Ninguém olhou para a tabela pai. No staging a mesma migration levou 574 ms.

O mecanismo: todo DDL pede acesso exclusivo à estrutura das tabelas que toca. Enquanto **espera** por
ele, bloqueia todas as leituras e escritas novas nessas tabelas; enquanto **executa**, também. Em
tabela quente, qualquer uma das duas parcelas vira fila, e a fila vira indisponibilidade. Não importa
se havia processo longo: o erro é entrar na fila de uma tabela quente sem teto de tempo.

Era previsível lendo a migration e o código. É por isso que a análise é obrigatória.

## O procedimento

### 1. Listar toda tabela que o DDL trava

Para cada comando da migration, escrever as tabelas travadas. **Inclui as que o comando não nomeia:**

- a tabela **pai** de cada chave estrangeira criada ou removida (foi o ponto cego do CLS-4540);
- a tabela filha, quando o DDL é na pai e há chave estrangeira apontando para ela;
- as duas tabelas de um `RENAME`.

Tabela criada na própria migration não conta: ninguém a usa ainda. Tudo o que já existe, conta.

### 2. Medir cada tabela em produção

Staging e preprod **não são evidência**: têm ordens de grandeza menos dado e menos tráfego. Para cada
tabela da lista:

- **Tamanho:** linhas e bytes. Decide quanto tempo o DDL executa.
- **Uso:** quem lê e escreve nela, e com que frequência (endpoints, crons, workers). Sai do código e
  das métricas. Decide se ela é quente.
- **Algoritmo do DDL:** instantâneo, online ou cópia da tabela. Decide se o tempo de execução cresce
  com o tamanho.
- **No momento do deploy:** transações abertas há muito tempo no banco. É um retrato, não uma
  garantia; por isso o passo 3 não depende dele.

Como medir em cada projeto (consultas, quem tem acesso a produção) está no overlay. A medição entra
no plano como número, com a data em que foi tirada.

### 3. Teto de espera, sempre

Todo DDL sobre tabela existente roda com um limite curto de espera pelo lock (poucos segundos, abaixo
do timeout das leituras da aplicação). Se não conseguir o lock, o comando falha, a fila se desfaz, o
deploy falha limpo e é repetido.

Isto **não é opcional** e não depende do que o passo 2 achou: é a única proteção contra o que a
medição não vê.

Junto com o teto, **uma checagem de existência por comando**, nunca um `if` em volta de um bloco. DDL
não é transacional: a migration pode falhar no meio, e a nova tentativa precisa continuar de onde
parou em vez de pular o que faltou.

### 4. Se houver risco, não fazer daquele jeito

Risco é: tabela quente na lista, ou DDL cujo tempo de execução cresce com uma tabela grande. A saída
depende do achado e fica **aberta**; o plano escolhe uma e escreve o motivo:

- seguir como está, porque o teto de espera e o tempo de execução medido cabem;
- redesenhar para não tocar a tabela quente. Chave estrangeira para tabela quente responde no plano:
  "esta chave vale o lock na tabela pai?". Às vezes não vale (log, histórico); quando o órfão é dado
  quebrado, vale, e fica com o teto;
- separar o DDL do deploy do código (PR e deploy próprios, antes);
- rodar em horário calmo, com alguém olhando e pronto para cancelar;
- outra saída que o caso pedir.

"Não achei risco" também é um resultado, e também fica escrito, com a lista e os números.

### 5. Registrar no plano e nas instruções de deploy

O plano leva: a lista de tabelas travadas, a medição de cada uma, o teto de espera, a saída escolhida
e o motivo. É conteúdo técnico do plano, escrito para o time (`rules/writing.md`).

As instruções de deploy (`skills/deploy-instructions.md`) levam o que quem faz o deploy precisa: quais
tabelas a migration trava, o que acontece se ela falhar por espera (repetir o deploy) e como
reconhecer que é ela que está segurando o banco.

## No review

Migration sem essa análise no plano é achado **bloqueante**, nosso ticket ou de outro. O revisor refaz
o passo 1 lendo a migration, não confia na lista do autor: a tabela que falta na lista é justamente a
que derruba.

## Limite de alcance

Esta regra é do nosso fluxo e fica do nosso lado (decisão do Lucas, 2026-11-18: não propor ao
playbook do time). Os revisores automáticos do SDD do projeto não a conhecem; quem a aplica somos nós,
no plano e no passo 13, inclusive ao revisar ticket de outro.

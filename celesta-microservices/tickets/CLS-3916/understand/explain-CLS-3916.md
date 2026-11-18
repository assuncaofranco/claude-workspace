# explain CLS-3916 — 2026-11-16 07:56

**Objetivo**

Começar o CLS-3916 só pelas partes que já estão decididas. O resto espera as respostas do PO e do Marcello, porque é ali que as decisões abertas mudam o resultado. O front já começou sem esperar.

**Premissas**

1. A Story foi dividida em 10 sub-tasks, espalhadas por 7 repositórios. Nenhuma tem plano ainda, mas o front (4776) já está em andamento.
   `searchJiraIssuesUsingJql parent = CLS-3916` · `git branch -r` nos 6 repos: nenhuma branch 47xx

2. Três sub-tasks só preparam o terreno e não dependem de nenhuma pergunta aberta. O 4767 cria o nome do novo tipo de prêmio, o 4768 cria o novo tipo de origem "promotion" no evento de activity, e o 4769 faz a activity aceitar esse tipo.
   Descrições das sub-tasks no Jira

3. As três perguntas ao PO caem todas no momento em que o gift é criado (4772).
   - Qual motivo o gift recebe? O CLS-3316, que define isso, ainda está em Split.
   - A tela Gifts to order já existe? O CLS-3865 ("complete gifts to order") também está em Split.
   - Quem fica sabendo quando um gift é pulado?

   `CLS-3316` e `CLS-3865`: status Split

4. Uma decisão é do Marcello: como guardar de onde o gift veio, se foi um usuário do BO, um cenário ou agora uma promoção. Uma opção é uma tabela nova, que exige migrar os gifts existentes e depois apagar as colunas antigas. A outra é só mais uma coluna, igual às duas que já existem. A escolha muda o 4770 e o 4773, e com eles os dados que já estão em produção.
   `Gift.php:81-86`: `source_user_id`, `source_scenario_id`

5. A promotion nunca enviou eventos para a activity, o histórico do jogador no BO. Para enviar, ela precisa de um canal configurado na infraestrutura, a fila. Nenhuma sub-task pede essa configuração.
   `celesta-promotion/config/packages/messenger.yaml:24-27`: sem rota para `UserActivityJob`

**Inferência**

Por isso, a Story anda em três ondas. Cada onda começa quando a pergunta que a trava for respondida, não quando a anterior terminar.

```
HOJE: planejar em paralelo
  4767 nome do tipo de prêmio "gift"
  4768 tipo de origem "promotion" no evento de activity
  4769 activity passa a aceitar esse tipo
        │
ESPERA RESPOSTA
  4770 origem do gift ............ ◄── Marcello: tabela ou coluna?
  4771 gift como prêmio na promoção ◄── PO: motivo (1)
  4772 criar o gift ao premiar ... ◄── PO: (1), (2), (3)
                                   ◄── fila da promotion para a activity
        │
DEPOIS
  4774 / 4775 BO ──► 4776 front (já começou: corre risco de refazer)
  4773 apagar colunas antigas (uma release depois do 4770)
```

A ação é uma só: mandar as três perguntas ao PO e a da origem ao Marcello, rodar o `/sdd-plan` nas três sub-tasks de cima, e avisar o Dimitris de que o 4776 está à frente do BO.

**O que falta**

Eu recomendo a coluna, mas a decisão ainda é do Marcello.

Também não confirmei se configurar a fila exige um pedido ao time O. Hoje é só uma suposição.

# CLS-418 — o que entendemos (2026-11-12)

Hoje os KPIs do player vêm de três lugares: Statistics, a tabela legada da Wallet e contadores do
Payment. O ticket faz BO, Gateway e Segment lerem só da Statistics, e o Payment parar de guardar os
dois contadores de payin. Nenhuma resposta de API muda, só a fonte.

## A ideia da nossa parte (pela spec; mecanismo não visto no código)

Nenhum endpoint novo recebe dado. A Statistics já consome eventos de pagamento, carteira e jogo e
calcula KPIs. "Ganhar" os KPIs novos é:
- calcular saques pendentes e generosity a partir de eventos que ela já recebe;
- **alterar** o endpoint por player existente: campos novos na resposta;
- **criar** uma leitura em lote, por domínio e por dia, para o Segment.

Payment: devolver `successfulPayinAmount`/`successfulPayinCount` lidos da Statistics e apagar as
colunas.

## Em aberto

- Se os eventos de pedido e cancelamento de saque já chegam na Statistics. Se não, passo a mais.
- Sub-tasks: nós fazemos todas, inclusive BO (3526), Gateway (3524) e Segment (3527); o time dono
  aprova o merge. Os components errados (3524, 3526) se ajustam quando formos trabalhar nelas.
- Perguntas da spec, donas do Viorel: moeda não padrão no BO; dropar as colunas agora ou depois.
  Não bloqueiam começar; voltam quando chegarmos nas sub-tasks que dependem delas.

# evaluate CLS-3916 — 2026-11-16 07:51

Sim, o CLS-3916 pode começar. O problema de negócio está claro, mas antes de planejar o código do gift faltam três respostas do PO e uma do Marcello.

## Onde está

- A Story está em Split desde 09/11. No Jira só há um comentário, o de custo do split.
- Nenhuma das 10 sub-tasks tem branch ou plano. Nos 6 repos, as únicas branches que existem são as do CLS-3247.
- O 4776 (front, Dimitris) já está In Progress, mas depende do 4774 (BO), que não começou. Ou seja, o front está sendo feito antes de o BO definir o que vai receber.
- Dos tickets que bloqueiam a Story, o CLS-3247 e as sub-tasks 4032, 4034 e 4035 estão Done. O CLS-3316 continua em Split.

## Necessidade de negócio

Está clara. A spec diz quem sofre hoje, como medir o sucesso, o que entra e o que fica fora. Vale o que concluímos antes: o gift passa a ser um prêmio da promoção e segue as regras de bônus de promoção.

## O que o split não cobre

1. **A promotion não envia activity hoje.** O `messenger.yaml` dela só tem rota para `TransactionalEmailJob`, `NotificationJob` e `GiftEventJob`. Hoje quem envia o `gift_offered` é o BO (`UserActivityJobManager.php:182`). O 4772 pede que a promotion envie esse evento, mas nenhuma sub-task prevê a rota, a fila e as configurações de deploy para isso. Isso deve virar um pedido ao time O.
2. **O gift precisa sair do loop de bônus.**
   - Se o jogador não tem moeda, `RewardHandler.php:206` encerra antes de olhar qualquer prêmio. O critério de aceite manda criar o gift mesmo assim.
   - `RewardHandler.php:227` trata todo prêmio que tem configuração como bônus.
3. **Replay de idempotência.** `GiftController.php:325-326` lê `source_user_id` e `source_scenario_id` direto no SQL. Se o 4770 não migrar esse trecho, o drop de colunas do 4773 quebra o replay.
4. **Gift duplicado.** Quando um bônus do mesmo tier falha na wallet, `RewardHandler.php:240` deixa a instância como não premiada e ela é processada de novo. O gift já tem uma restrição de unicidade por jogador e chave (`Gift.php:30`); falta definir a chave do gift de promoção (instância × prêmio) para que ele não seja criado duas vezes.

## Perguntas ao PO (Francisco)

1. **Motivo do gift.** O critério de aceite diz que o gift recebe "o motivo da configuração (CLS-3316)". Só que o 3316 está em Split. Hoje a configuração de gift só tem o `reason` antigo (`RewardConfiguration.php:179`), e o gift já usa o novo `reason_id`. Esperamos o 3316 ou copiamos o motivo que existe hoje?
2. **Gifts to order.** O CLS-3865 também está em Split e não tem link com a Story. O critério "aparece em Gifts to order" espera o 3865 ou sai deste ticket?
3. **Gift pulado.** Quando a configuração foi desativada, o critério manda "registrar o skip". O operador vê isso em algum lugar? Se ficar só no log da aplicação, o jogador ganha o prêmio, ninguém encomenda o presente e ninguém percebe.

## Pergunta ao Marcello, que fez o split

A opção é entre a entidade `Source`, que exige backfill e um drop depois (4770 e 4773), e uma coluna `source_promotion_id` ao lado das duas que já existem.

Eu prefiro a coluna. A `Source` custa duas sub-tasks, um backfill na tabela inteira e um deploy em duas releases. O ganho dela é um modelo limpo para uma quarta origem de gift, mas segmento e bulk estão explicitamente fora do escopo. Só compensa se já houver plano para essas origens.

## Riscos

| Área | Risco |
|---|---|
| Dinheiro | O gift não passa pela wallet, mas o valor dele entra nas estatísticas de gift (`GiftEventJob`). O risco concreto é o gift cair no caminho dos bônus (item 2). |
| Contratos | O `promotion` é um tipo de origem novo: a activity (4769) precisa aceitá-lo antes que a promotion comece a enviar. A API de gift ganha `sourcePromotionId`, que o BO consome no 4775. A rota do jogador deixa o gift de fora. |
| Dados | Backfill de todos os gifts existentes, e o drop das colunas uma release depois. |
| Deploy | São 7 repos e 2 bibliotecas com tag. A ordem: constants e job-library, depois activity, promotion 4770, 4771 com 4772, BO, front, e o 4773 na release seguinte. Hoje a promotion recusa configuração de gift como prêmio (`RewardSubscriber.php:99`). O 4771 tira essa trava; se ele for para produção antes do 4772, só o BO impede que alguém salve um gift como prêmio. |

## Próximo passo

1. Mandar as 3 perguntas ao PO e a pergunta da `Source` ao Marcello.
2. Enquanto as respostas não chegam, rodar `/sdd-plan` em paralelo no 4767, 4768 e 4769, que não dependem delas.
3. O 4770 espera o Marcello. O 4771 e o 4772 esperam as perguntas 1 e 3 e a decisão sobre a fila de activity.
4. Avisar o Dimitris de que o 4776 está sendo feito antes de o BO definir o que vai receber.

Quer que eu escreva as perguntas em inglês para você mandar?

---

O conector do Atlassian continua no endpoint V1, que sai do ar em 2027-03-01. Para corrigir, remova o conector e adicione de novo pelo diretório de conectores.

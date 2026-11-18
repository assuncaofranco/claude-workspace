# CLS-1214 — o que entendemos (2026-11-12)

O que a spec diz está no Jira. Aqui fica só o que entendemos e o que falta.

## O fluxo

1. O player pede um saque. Pode pedir outro antes de o primeiro ser pago; cada pedido é um registro
   (withdrawal request) com valor e status próprios. Não há divisão por tipo de dinheiro: o saque sai
   do saldo sacável. Sub balance (bônus) não entra.
2. O operador valida no BO.
3. Depois de uma espera, o job `withdraw-request:payout-delay` da wallet
   (`src/AppBundle/Command/PayoutDelayCommand.php`) pega os pedidos validados e manda ao provedor
   automático. Frequência: não vista.
4. **O que muda:** o job passa a montar um envio por grupo (mesmo player, mesma moeda, Bank Transfer
   auto), não um por pedido. Players diferentes continuam em envios separados.
5. O provedor (Genome ou My.Tu) faz **uma** transferência direto para a conta do player, com o total.
   No extrato: um crédito de 4000, referência "4290150, 4292746, 4301966".
6. No site da brand: os pedidos continuam separados, cada um com valor e status.
7. No relatório financeiro (BO): a linha do payout mostra os ids dos **pedidos de saque**.

Ganho: uma taxa bancária por grupo em vez de uma por pedido.

## Sub-tasks

Nós fazemos todas; o time dono do repositório aprova e faz o merge.

- 4753 payment: aceitar lista de ids no payout, descrição com todos, guarda de duplicidade para todos.
- 4755 wallet: agrupar no job, propagar paid ou error ao grupo inteiro.
- 4754 statistics: guardar os ids no movimento do payout, para o relatório.
- 4756 backoffice: expor todos os ids nas linhas do relatório de transações.
- 4757 backoffice-front (F): mostrar os ids nas linhas de payout.
- 4758 backoffice: tirar o id único das linhas do relatório (cleanup).

Ordem pelos Blocks: 4753 → 4754 ∥ 4755; 4754 → 4756 → 4757 → 4758. O cleanup (4758) só entra
depois que o front (4757) já mostra a lista.

## Respondido pelo código (2026-11-12)

- **Falha do payout combinado.** Um pedido em `error` pode voltar a `pending`, ir para `refused` ou
  `canceled`, pedido a pedido no BO (`WithdrawRequestConstants::STATUS_TRANSITIONS`, constants da
  wallet). Com o grupo, os pedidos caem juntos em erro e o operador trata cada um como hoje; os
  revalidados entram no próximo job e são reagrupados. Nada novo a construir, nada a perguntar.
- **Aviso ao player.** A wallet manda email a cada mudança de status de cada pedido, inclusive `paid`
  (`TransactionalEmailListener.php:108`). Com o grupo, um email por pedido, cada um com seu valor.

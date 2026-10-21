# 2026-10-08 — Celesta Game Command Job above 1.0 Errors, game:big-winner

Uma falha isolada às 11:15 UTC (celesta-game v1.806): `BigWinner::setFirstName(): Argument #1 must be of type string, null given`, em `BigWinnerTransformer.php:31`. As execuções seguintes passaram. Roda como o CronJob `game-recalculate-big-winners` em `celesta-prod-1`, a cada 15 min, com `ttlSecondsAfterFinished: 300`: o pod some e o log fica só no Datadog.

**Causa raiz, seguida pelo código:**
- **game:** `BigWinnerCommand` → `MemberzoneClient::getCustomers` (POST `/{locale}/api/customers` no CRM) → `BigWinnerTransformer`. O game repassa a resposta sem tratar.
- **crm (v1.728):** `CustomerListController::getCustomersAction` lê do **MySQL** via DBAL (`CustomerListRepository::getCustomersList`, tabela `li_customer`), não do Elasticsearch. O `CustomerNormalizer` devolve `first_name` direto. A coluna é `nullable: true`.
- **CLS-1837** (commit `57a4c99b0c`, PR #2052, em prod desde 2026-07-23 com o crm v1.703): no cadastro (POST), nome, sobrenome, telefone, endereço etc. ficaram **opcionais para marcas não-ANJ** (`CustomerType::buildForm`, `$optionalFieldOptions`).
- **game:** `BigWinner::setFirstName(string)` e `setLastName(string)` ainda exigem string. O contrato mudou no CRM, e o consumidor não acompanhou.

**Jogador CONFIRMADO: 2415678, domínio 53, carteira 2411111 (CLP).** Na wallet ele tem vários `win` com sucesso entre 11:06 e 11:15:31 (o maior: 1.900 às 11:15:14), além de um depósito às 11:13. O caminho até a wallet: `wallet.owner_id` → `transaction.wallet`, usando o índice `idx_wallet_status_transaction_at`. Os tipos de prêmio são `win`/`bonus_win` com `status = 'success'` (de `Lancaster\Constants\Wallet\TransactionConstants`).
**Histórico da identificação:** No meio do caminho eu o descartei errado. Os prêmios que ainda estavam em `big_winner` eram das 11:30, mas a tabela **só guarda 2 horas**: o cron passa `--from = now - 120 min` e `deleteFromDate` apaga o que é anterior. O prêmio dele entre 11:00 e 11:15 já tinha sido apagado quando consultamos de novo (a mesma janela voltou com 0 linhas). **Lição: `big_winner` é volátil. Para reconstruir um lote, a fonte é a transação na wallet, não essa tabela.** Prova pendente: transação de prêmio do 2415678 na wallet entre 11:00 e 11:15 UTC (EXPLAIN antes, porque a tabela é enorme). Cadastro às 10:35:53, `updated_at` às 11:28:32 (entre a falha e a execução seguinte). Achado cruzando `big_winner` (game, `transaction_at` entre 11:00 e 11:15:31, 210 jogadores) com `li_customer` (CRM, `updated_at` entre 11:15 e 11:31, 6 resultados, só ele recente). As queries rodadas pelo Lucas, com EXPLAIN antes. Ressalva: o `updated_at` não prova que o campo alterado foi o nome.

**Agravantes no código do game:**
- Um jogador sem nome derruba o lote inteiro.
- `catch (\Exception)` não pega `TypeError`.
- O ponto de partida do job é global (`getMaxTransactionId`). Se o nome tivesse ficado vazio de vez, o big winner teria parado para todos os domínios.

**Saída:** reportar. A correção é do time do game (aceitar null, ou pular o jogador). Vale procurar o mesmo padrão em outros consumidores de `/api/customers`.

**Armadilha: o status do CronJob não serve.** O cron roda `php -r '... exec("php bin/console game:big-winner ...")'`, e o `exec` ignora o código de saída do comando. O Job do Kubernetes termina como Complete e o `lastSuccessfulTime` avança **mesmo quando o comando quebra**. Em 2026-10-09 isso me fez dizer "já recuperou" errado. A verdade está nos traces do Datadog (`resource_name:game:big-winner`).

**Dica operacional:** o `GROUP_CONCAT` do MySQL corta em 1.024 caracteres (`group_concat_max_len`). O `SET SESSION` não pegou no cliente do Lucas, então o jeito foi paginar por `player_id >`.

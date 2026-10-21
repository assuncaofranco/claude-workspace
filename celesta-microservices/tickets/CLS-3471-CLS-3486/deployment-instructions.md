# CLS-3471-CLS-3486: Deployment instructions

## Ordem

```
1. Merge do PR celesta-game-go CLS-3471-CLS-3486 → CLS-595
2. Deploy do celesta-game-go quando a CLS-595 for implantada (não há deploy próprio deste ticket)
```

**Não há ordem entre serviços:** só o celesta-game-go muda.

Sem migration, sem variável de ambiente nova, sem fila nova, sem biblioteca, sem PR no proteus.

---

## Por quê

O ticket muda só o **conteúdo** que o game-go grava em `game_transaction.errors` depois de uma
chamada à carteira que falhou. A linha já ficava `FAILURE` antes; agora o `errors` traz o que o PHP
celesta-game grava (código da carteira primeiro), em vez do texto interno do Go.

Quem lê a coluna é o celesta-game (PHP), no `POST /api/game-transactions` que o backoffice consome.

| Estado | O que acontece |
|---|---|
| game-go novo, PHP atual | o PHP lê a coluna como `json` → array (`Entity/GameTransaction.php:49`) e a devolve como está (`GameTransactionNormalizer.php:52-64`). O formato novo é exatamente o que o próprio PHP grava, então não há formato que ele não conheça. |
| linhas antigas do game-go | continuam com `["wallet: http 400 (code=3)"]`. Não são reescritas, e o PHP lê as duas formas. |

O game-go não lê essa coluna em lugar nenhum: só escreve (`internal/games/transactions.go`).

## Rollback

Reverter o celesta-game-go sozinho é seguro. As linhas gravadas no formato novo ficam como estão,
e o PHP lê os dois formatos.

## Infra

Nada novo. Um ponto a conferir, que **não bloqueia** o deploy:

- A mensagem gravada inclui a URL da carteira que o serviço tem configurada, por exemplo
  `[3, "HTTP/1.1 400 Bad Request returned for \"<WALLET_HOST>/api/domain/…\"."]`. Ela só sai igual
  à do PHP se `WALLET_HOST` do game-go e do celesta-game apontarem para o mesmo host no ambiente.
  Localmente não apontam: o PHP usa `http://walletweb.docker/` e o game-go `http://wallet.nginx:80`.
  O Proteus só compara o código (`errors[0]`), então isso não quebra a suíte. A diferença aparece
  só no texto que o suporte vê.

## O que observar depois

- Uma aposta acima do saldo, via SoftGamings ou Quanta, grava `game_transaction.errors` começando
  pelo código inteiro, por exemplo `[3, …]`.
- **Log novo:** `wallet call failed` em cada falha de carteira. É warning para os códigos 3 a 6 (saldo
  insuficiente, limite de aposta, aposta não permitida, restrição de bônus), como no PHP, e error para
  o resto. Antes, o SoftGamings não logava esse erro. Pode subir o volume de warnings no Datadog do
  game-go.
- Proteus `softGamingsWebhookWallets.pcgg-10.test.ts`, passo "Failed transaction stored", verde.

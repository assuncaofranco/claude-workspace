# CLS-1872 — Deployment instructions

Para colar no épico e nos PRs. A pergunta aqui não é "quando a feature fica pronta" — é **em que ordem
o deploy pode acontecer sem derrubar nada em produção**. A feature só existe inteira no fim; qualquer
estado intermediário tem que ser inofensivo.

---

## Ordem

```
1.  celesta-game       CLS-2978   (campos na listagem)
2.  celesta-game       CLS-2979   (POST + PUT)
3.  celesta-backoffice CLS-2980   (policy + gate de leitura)   ← roda migration
4.  celesta-backoffice CLS-2978   (mapeia os campos, esconde options)
5.  celesta-backoffice CLS-2979   (proxy de escrita)
```

**Regra curta: o game inteiro antes do backoffice.** Dentro de cada serviço, a ordem dos tickets é a
da pilha de PRs, e o GitHub já a força — cada PR tem o anterior como base.

---

## Por quê

**O game é passivo; o backoffice é quem chama.**

O CLS-2979 do backoffice faz `POST`/`PUT` em `api/domain/{id}/game-gateways` do game. Se o backoffice
for primeiro, essa rota ainda não existe: o game devolve 404/405, o `handleV2Exception` converte em
404 ou 400, e o operador vê "erro ao salvar". Não derruba nada, mas entrega um botão que não funciona.

No sentido contrário não há efeito: o game 2979 são rotas novas que ninguém chama até o backoffice
subir. Código morto, literalmente.

**O game 2978 é o único que mexe em caminho existente.** Ele acrescenta `options` e
`freeRoundsCancelable` à expressão `NEW` do DQL de `getConfigurationsByDomain()` — a consulta que já
serve o `GET` de hoje. Não é aditivo puro, é alteração de uma query em produção. Por isso vai primeiro
e sozinho: se algo estiver errado ali, aparece isolado, sem nada em cima.

**Quem consome esse `GET` do game:** só o `GameClient` do celesta-backoffice
(`src/Library/GameClient.php:437`). O Proteus consome `/api/game-gateways`, que é outro endpoint (a
listagem global, `getProviders()`), **não tocado** por este épico. Verificado por busca em todos os
repositórios em 2026-09-23.

---

## Cada passo pode ir sozinho?

| # | Deploy | Pode ir sozinho? | O que acontece enquanto o resto não subiu |
|---|---|---|---|
| 1 | game 2978 | **sim** | o `GET` passa a devolver dois campos a mais. O backoffice antigo monta a resposta escolhendo chaves uma a uma, então ignora o que não conhece |
| 2 | game 2979 | **sim** | rotas novas sem chamador. O validator e o `fromEntity` só existem nesses caminhos |
| 3 | bo 2980 | **sim** | a migration cria a policy; o gate passa a **aceitar mais** permissões, ninguém perde acesso. A resposta não muda |
| 4 | bo 2978 | **sim** | passa a repassar os dois campos, e a esconder `options` de quem não tem EDIT |
| 5 | bo 2979 | **sim** | os dois endpoints de escrita passam a existir |

Nenhum passo quebra produção sozinho. O que varia é **quanto da feature funciona** no meio do caminho.

---

## O caso que já foi problema, e não é mais

Se o **backoffice 2978 subir antes do game 2978**, o backoffice procura dois campos que o game ainda
não manda. A primeira versão lia as chaves direto — e uma chave ausente vira `ErrorException` neste
projeto, ou seja **500 na listagem para todo mundo**, num endpoint que hoje funciona. Regressão de
verdade, em produção.

Foi corrigido: o normalizer usa `array_key_exists` e **omite** a chave que não veio, em vez de
inventar valor. A listagem responde 200, apenas sem os dois campos.

Isso significa que a ordem game→backoffice é **recomendada, não obrigatória**. Um rollback do game
sozinho também deixou de ser perigoso — e essa é a razão de ser da correção, já que ordem documentada
é garantia mais fraca do que código que não quebra.

---

## Migration

Só o **bo 2980** tem migration (`Version20260921000000`), e ela roda no job `migration` do CI antes do
deploy (`.github/workflows/ci.yml:15`).

- Idempotente: `INSERT IGNORE` nas quatro tabelas, todas com o índice único necessário.
- O `down()` remove **só** o que ela criou: a policy nova, o vínculo em `policy_permission` e o
  `role_policy`. **Não** apaga a linha de `permission`, que pertence à migration do CLS-1821 e continua
  referenciada pela policy `PS_GAME_CONNECTIONS_EDIT`.
- Não depende dos outros quatro deploys, em nenhuma direção.

---

## Rollback

Qualquer um dos cinco pode voltar sozinho.

- **bo 2979** volta → os endpoints de escrita somem; a leitura continua.
- **bo 2978** volta → `options` some da resposta; nada quebra.
- **bo 2980** volta → o gate volta a exigir `PS_INTEGRATIONS_READ`. Quem tiver só a policy nova perde
  a listagem. Rodar o `down()` só se quiser remover a policy; deixá-la não faz mal.
- **game 2979** volta → as escritas do backoffice passam a receber 404. O operador vê erro ao salvar.
- **game 2978** volta → o backoffice para de receber os dois campos e, pela correção acima, apenas
  deixa de exibi-los.

---

## O que observar depois de cada deploy

Depois do **bo 2978**, a lista passa a carregar credencial de provedor para quem tem
`PS_GAME_CONNECTIONS_EDIT`, e isso **já chega ao navegador**. Uma redação anterior desta seção dizia
que o front em `master` não consumia `game-providers`; é falso. A tela de Integrations despacha
`getGameProviderConnections` (`administration/integrations/index.js:46`), que passa por
`store/reducers/integrations.js:95` e faz o `GET`. O payload inteiro entra no Redux e na aba de rede;
o que só começa com o **CLS-2981** é a *exibição* do `options` num formulário. Para a AC de não expor
credencial a quem não tem EDIT, o que conta é o deploy do bo 2978, não o do front.

Depois do **bo 2979**, o primeiro `POST`/`PUT` real chama o provedor de dentro da requisição. Para a
maioria dos tipos essa chamada baixa o catálogo inteiro, então a latência do save é a do provedor, não
a nossa. O backoffice espera até 60s (`CurlClient::EXTENDED_REQUEST_TIME_LIMIT`).

---

## Os caminhos mudaram, e o front precisa acompanhar

O bo 2979 tira a listagem de `/integration/game-providers`. Não há mais alias para o caminho antigo:
a rota legada existiu por alguns dias e foi removida a pedido, porque a rota e a tela são novas e o
deploy é de feature nova.

Os caminhos finais seguem a regra de número — plural quando a resposta traz muitos, singular quando
traz um:

| Verbo | Caminho |
|---|---|
| `GET` | `/api/gateway/domain/{domainId}/game/game-providers` |
| `POST` | `/api/gateway/domain/{domainId}/game/game-provider` |
| `PUT` | `/api/gateway/domain/{domainId}/game/game-provider/{id}` |

**Sem a troca no front, a lista quebra em silêncio.** O thunk engole o erro de propósito (sem
`handleError`, com comentário explicando) e `integrations/index.js:70` só renderiza com
`!gameProviders.error`, então os cards perdem o badge de status sem erro nenhum na tela.

São duas linhas em `src/services/workers/integrations.js` — o `GET` da linha 4 e o `PUT` da linha 8.
O `PUT` muda duas vezes: sai de `integration` e vai para o singular.

---

## Fora de escopo, mas ligado ao deploy

O sidecar nginx do celesta-game registra corpo de requisição e de resposta. A partir do **bo 2978** e
do **bo 2979** há credencial de provedor nesses corpos. É ticket do DevOps, acompanhado em separado —
registrado aqui só para que a decisão de quando deployar seja tomada sabendo disso.

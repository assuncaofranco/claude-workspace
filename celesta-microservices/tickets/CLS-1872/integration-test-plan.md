# CLS-1872 — Plano de teste de integração

Teste **entre tickets**, não de cada ticket. Cada subtask tem os seus próprios testes; aqui se prova
que os quatro juntos entregam o que o ticket pai promete.

Entrada só pelo **Backoffice** (API e tela). Nada de chamar o celesta-game direto, nada de escrever
no banco — senão o teste não prova que o operador consegue fazer aquilo.

Escrito em 2026-09-21, antes da implementação. Revisar quando o CLS-2979 estiver pronto: os itens
marcados **(confirmar)** dependem de como a validação ficou.

---

## 1. A restrição que define o plano

O CLS-2979 não valida `options` contra um schema. Ele **monta o cliente do provedor com as options
enviadas** e, quando o provedor tem uma chamada de leitura, **pinga o provedor de verdade**.

Consequência: não existe "criar uma conexão de mentira para testar". Ou as credenciais funcionam, ou
o save é rejeitado. Isso força três escolhas antes de começar.

### 1.1 Quase todo tipo pinga o provedor — corrigido em 2026-09-22

A classificação anterior desta seção estava errada. Ela separava os tipos por "tem sincronizador",
e concluía que cinco passavam pela validação sem tocar a rede. O critério certo é **qual chamada o
validator sabe fazer**, e o validator resolve isso por um `match` no tipo, construído a partir dos
sincronizadores.

| Grupo | Tipos | O que acontece no save |
|---|---|---|
| **Pingam o provedor** (13) | betsoft, bongo, playn_go, pragmatic, redgenn, relax, wazdan, yggdrasil (`getGames`); quanta (`gamesList`); evolution (`getAvailableGamesList`); git_slot_park (`getGameList`); gamble_hub (`getCurrencies`); soft_gamings (`getGameFullListStream`) | checagem de chaves **+ chamada real ao provedor** |
| **Só checagem de chaves** (1) | aleaplay | o sincronizador dele começa com `graphQlQuery(string $query)`, que exige uma query — pingar acoplaria o validator ao schema GraphQL deles |
| **Sem cliente na factory** (5) | aleaplay_v2, soft_gaming, absolute_live_gaming, bet_soft, reelsoft | a factory lança, o save é rejeitado com 400 |

**Escolha do tipo para o caminho feliz automatizado: `gateway_type_aleaplay`.** É o único que passa pela
validação inteira sem depender de credencial real nem de rede, o que torna o teste repetível.

Ele exige quatro chaves: `secret_key`, `bonus_api_base_url`, `customer_api_base_url` e
`environment_credential`. Faltando qualquer uma, a factory falha e o save é rejeitado — que é como o
cenário 9 é exercitado.

Qualquer um dos treze do primeiro grupo serve para o cenário 16, e aí precisa de credencial real de
preprod.

### 1.2 O grupo C está fora de escopo

Esses 5 tipos estão em `TYPES` e não têm cliente na factory. Esconder ou depreciar tipos legados é
o CLS-2688, listado explicitamente como fora de escopo no ticket pai. **Não tratamos e não testamos.**

O que continua dentro do CLS-2979, e é só isto: `ProviderException extends \Exception`, então sem
captura o Symfony devolve `500`. O ticket pede *"reject with 400 and the validation or provider
error"*. Garantir o `400` é escopo; o resto não é.

### 1.3 Não assumir que chave faltando é rejeitada

A factory lê `$options['api_login']` direto. Em PHP 8 isso é **warning**, não exceção: a chave vira
`null` e a execução continua. Ou seja, uma configuração incompleta pode **passar** na validação do
CLS-2979.

Isso é comportamento atual do celesta-game e **não é nosso para consertar** — a factory está no
caminho do `launchGame()`, e endurecê-la arriscaria derrubar conexões antigas que hoje funcionam.

Para o teste, a consequência é só de redação: o cenário 9 **observa** o que acontece, não afirma
antecipadamente que dá `400`. O resultado é informação para o TL, não defeito a corrigir aqui.

---

## 2. Pré-requisitos

**Quatro perfis no Backoffice**, criados pela tela de Access control:

| Perfil | Policies concedidas |
|---|---|
| P0 | nenhuma de Integrations |
| P1 | Access integrations |
| P2 | View Game connections (a nova, do CLS-2980) |
| P3 | Update Game connections |

P2 **sem** Access integrations é de propósito: prova que a policy nova funciona sozinha, que é a
razão de ela existir.

**Uma marca de teste** sem conexão nenhuma com o tipo de gateway escolhido — o cenário 19 precisa do
estado vazio.

**Em preprod-1 dois desses perfis já existem** (verificado no banco em 2026-09-21): `product_owner`
é o P3 (Access integrations + Update Game connections) e `head_of_operations` / `acquisition manager`
são o P1 (Access integrations só). O P2 só existe depois que a migration do CLS-2980 for deployada —
hoje `PS_GAME_CONNECTIONS_SEE` não existe lá.

**Credencial válida de um provedor do grupo A** em preprod, para o cenário 16. Pedir ao time.

---

## 3. Cenários

Cada linha diz o que se faz e o que se observa. "Observável" quer dizer que a coleção consegue ler
de volta — não vale "funcionou".

### Leitura — CLS-2978 + CLS-2980

| # | Quem | Ação | Esperado |
|---|---|---|---|
| 1 | P0 | `GET .../integration/game-providers` | `403` |
| 2 | P1 | idem | `200`, array; **nenhum item tem a chave `options`** |
| 3 | P2 | idem | `200`; nenhum item tem `options` |
| 4 | P3 | idem | `200`; **todo** item tem `options` preenchido |
| 5 | P1 | idem | `freeRoundsCancelable` presente e booleano — é campo não sensível, vem para todos |

O cenário 3 é o coração do CLS-2980: hoje esse perfil toma `403`.

### Escrita — CLS-2979 (POST e PUT)

| # | Quem | Ação | Esperado |
|---|---|---|---|
| 6 | P1 | `POST` conexão | `403`; `GET` de P3 confirma que nada foi criado |
| 7 | P2 | `POST` conexão | `403`; idem |
| 8 | P3 | `POST` tipo do grupo B, options completas | sucesso; aparece no `GET` **imediatamente** |
| 9 | P3 | `POST` faltando uma chave obrigatória | **observar** o que acontece — ver 1.3. Se gravar, registrar e reportar; não corrigir aqui |
| 10 | P3 | `POST` tipo do grupo A, credencial errada | `400` com o erro do provedor; nada criado |
| 11 | P3 | `POST` segunda conexão do **mesmo tipo**, mesma marca | sucesso; as duas na lista, editáveis separadamente |
| 12 | P3 | `PUT` mudando só o `name` | `200`; `GET` mostra o nome novo e `options` intacto |
| 13 | P3 | `PUT` com options inválidas | `400`; `GET` mostra a conexão **exatamente como estava** |
| 14 | P3 | `PUT` tentando mudar o `type` | rejeitado — o ticket pai diz que só `name`, `options` e `enabled` são graváveis |
| 15 | P1 e P2 | `PUT` | `403`; registro inalterado |

O cenário 13 é o que mais dói se falhar: uma validação que rejeita **depois** de gravar deixa a marca
com credencial quebrada.

### Efeito no produto — o que prova que serviu para alguma coisa

| # | Ação | Esperado |
|---|---|---|
| 16 | Criar conexão de um tipo do grupo A com credencial real, rodar o sincronizador | os jogos daquele provedor passam a existir para a marca |
| 17 | `PUT` com `enabled: false` | os jogos daquele gateway saem do lobby da marca — **(confirmar com o Marcello**, o ticket pai marca isso como suposição) |

Sem o 16, tudo acima prova só que o CRUD grava linha. O 16 é o que liga a conexão ao objetivo do
ticket pai.

### Segurança

| # | Ação | Esperado |
|---|---|---|
| 18 | Repetir 9, 10 e 13, e ler logs de celesta-game e celesta-backoffice | **nenhum valor de `options` em log ou mensagem de erro** |

Atenção: o CLS-2979 diz para repassar os erros do Game *"unchanged"*, e o erro vem de um provedor que
recebeu a credencial. Os dois requisitos se contradizem. Este cenário é onde isso aparece.

### Front — CLS-2981

| # | Quem | Ação | Esperado |
|---|---|---|---|
| 19 | P3 | abrir a marca sem conexão do tipo escolhido | estado vazio com ação de criar |
| 20 | P2 | abrir a página de detalhe | vê a lista; **não** vê o editor de JSON; sem botão de salvar |
| 21 | P3 | abrir, editar, salvar com options inválidas | erro do backend aparece no formulário, não como erro genérico |
| 22 | P3 | alterar `freeRoundsCancelable` e salvar | confirmação com o aviso obrigatório sobre efeitos inesperados |

---

## 4. Fora do teste de integração

- **Cada combinação de permissão isolada** — são 8 por endpoint, e já estão nos testes do CLS-2980.
  Aqui entram só os 4 perfis que existem de verdade na operação.
- **Cada um dos 19 tipos de gateway** — a permissão e o filtro de `options` não ramificam por tipo.
  O que ramifica por tipo é a validação, e isso é coberto pelos grupos A/B/C em 1.1.
- **O grupo C** — fora de escopo (CLS-2688). Não testamos e não tratamos.
- **Qualquer correção no `GameGatewayClientFactory`** — está no caminho do `launchGame()` e nada no
  ticket pai pede para mexer nele. Observamos o comportamento atual e implementamos contra ele.

---

## 5. Ordem de execução

O plano só roda inteiro quando os quatro tickets estiverem em preprod. Antes disso:

| Já entregue | Cenários possíveis |
|---|---|
| CLS-2980 | 1, 3 (o 2 e o 4 sem `options`, com valor limitado) |
| \+ CLS-2978 | 2, 4, 5 |
| \+ CLS-2979 | 6 a 15, 18 |
| \+ CLS-2981 | 19 a 22 |
| tudo + credencial real | 16, 17 |

---

## 6. Execução — 2026-09-21

A coleção `CLS-1872.postman_collection.json` (runbook em `CLS-1872.md`) cobre os cenários que rodam
só pelo Backoffice. Newman: **15 requests, 32 assertions, 0 falhas**, contra as branches
`CLS-1872-integration` dos dois repositórios.

| Cenário do plano | Coberto pela coleção |
|---|---|
| 1 (sem permissão → 403) | sim — passo 12 |
| 2, 3 (READ / SEE sem options) | **não** — ver limitação abaixo |
| 4 (EDIT com options) | sim — passo 2 |
| 5 (`freeRoundsCancelable` presente) | sim — passo 2 |
| 6, 7 (POST sem permissão) | sim — passo 13 |
| 8 (POST válido) | sim — passo 3 |
| 9 (chave faltando) | não — precisa de um tipo com ping |
| 10 (credencial errada) | não — precisa de credencial real de preprod |
| 11 (segunda conexão do mesmo tipo) | sim — passo 5 |
| 12 (PUT válido) | sim — passo 6 |
| 13 (PUT inválido não altera nada) | sim — passos 8 e 9 |
| 14 (PUT tentando trocar o tipo) | sim — passo 10 |
| 15 (PUT sem permissão) | sim — passo 14 |
| 16, 17 (sincronizador, lobby) | não — precisa de credencial real |
| 18 (options fora de log e erro) | não — inspeção manual de log |
| 19–22 (front) | não — CLS-2981 |

**Os dois perfis que faltam — corrigido em 2026-09-21.** Eu havia registrado que os perfis
*Access integrations only* e *View Game connections only* não seriam executáveis em lugar nenhum.
Errado: as fixtures alimentam apenas o banco de **teste**. Nos ambientes reais, inclusive produção,
as permissões são atribuídas à mão na tela de Access control. Logo os dois perfis são criáveis em
preprod como qualquer outro role — a migration só torna `PS_GAME_CONNECTIONS_SEE` **concedível**;
conceder é operação normal. Os passos estão no `CLS-1872.md`.

**Cross-check de documentação (passo 8 do processo `ticket-postman`):** a resposta real da listagem e
o schema `IntegrationGameProviderResponse` do `open-api.json` regenerado batem exatamente nos dois
sentidos — oito campos, nenhum documentado que não aparece, nenhum retornado que não está documentado.

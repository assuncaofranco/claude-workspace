---
name: cls1872-cls2980-findings
description: "CLS-2980 (permissões de game connections no Backoffice) — modelo de permissão verificado no código, matriz de variação, decisão do endpoint do gateway e os 3 bloqueios abertos"
metadata: 
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-21T08:52:37.191Z
---

# CLS-2980 — Add permissions to Backoffice

Filho de **CLS-1872** (Create and edit game gateway connections on Backoffice).
Documento interno de trabalho — **não** é o spec. O spec sai depois, via `/spec` do celesta-backoffice,
e leva só a seção de acceptance criteria derivada da matriz abaixo.

Estado em 2026-09-21: nenhuma branch de CLS-2979 nem CLS-2980 existe em nenhum repo
(`git branch -r --list "origin/CLS-29*"` em celesta-backoffice, celesta-backoffice-front, celesta-game).

---

## 0. Os quatro filhos do épico (Jira, 2026-09-21)

| Ticket | O que entrega | Status | Dono |
|---|---|---|---|
| **CLS-2978** | GET de game connections devolve **todos** os campos da gateway configuration — é quem cria o `options` | To Do | Lucas |
| **CLS-2979** | Salvar uma conexão editada valida a configuração — é onde nasce o caminho de escrita | To Do | Lucas |
| **CLS-2980** | Permissões no Backoffice — **este** | In Progress | Lucas |
| **CLS-2981** | Cards de game providers abrem lista e página de detalhe (front) | To Do | **outra pessoa** |

**Consequências desse quadro:**

- O CLS-2981 é do front e de outra pessoa. O item "canEdit hard-coded false" da descrição do CLS-2980
  **não é nosso** — e de todo modo não existe em master (ver seção 3).
- O `options` que o CLS-2980 manda esconder é entregue pelo **CLS-2978**. Não é divergência de regra:
  a regra ("SEE não vê options, EDIT vê") bate com o que concluímos. É **dependência de ordem**.
- Dependência real: **2978 → 2979 → 2980**. O 2980 está In Progress e os dois de que ele depende
  estão To Do — a ordem do Jira está invertida em relação à dependência.

### Decisão de sequência

Enquanto o 2978 não entrar, as partes do 2980 que **já podem ser feitas** são:
migration da policy nova, tradução, e o gate de acesso da listagem (`READ ∨ SEE ∨ EDIT`).

A parte que **não pode** ser feita antes do 2978 é o filtro de `options` e os testes das células 5 e 7
da matriz — sem o campo existir, esses testes passam verdes sem proteger nada (verde falso).

---

## 1. Decisões já tomadas (fora do código)

**Endpoint do celesta-gateway — daily de 2026-09-21.** O time criou um endpoint novo no
`celesta-gateway`, mas já existia um antigo equivalente. **Decisão: usar o antigo.** Alinhar com o
time de front antes de qualquer implementação que dependa disso.
Pendente: identificar exatamente qual é o antigo e qual é o novo — não foi verificado em código
ainda. Fazer isso quando chegarmos na parte de gateway/front, não antes.

---

## 2. O modelo de permissão, como está no código

Cadeia real, verificada:

```
role  →  role_policy  →  policy  →  policy_permission  →  permission  →  ROLE_OAUTH2_<PERMISSION>
```

- `OAuth2Authenticator::ROLE_PREFIX = 'ROLE_OAUTH2_'`
  — `src/OAuth2Bundle/Security/Authentication/OAuth2Authenticator.php:32`
- cada permissão vira uma role Symfony no token
  — `OAuth2Authenticator.php:129` (`array_walk($permissions, fn ($p) => $user->addRole(ROLE_PREFIX . strtoupper($p)))`)
- as permissões do usuário saem de `getPolicyPermissionNamesByUser()`
  — `src/UserBundle/Repository/RolePolicyRepository.php:33-41` → `getPolicyPermissionNamesByRole():43-58`

### Achado estrutural 1 — a query NÃO sobe na árvore de policies

`getPolicyPermissionNamesByRole()` faz `role_policy → policy → policy_permission → permission`.
Não há recursão em `policy.parent`.

Consequência: uma policy filha **não** herda as permissões da policy pai. Quem receber só a policy
nova `PS_GAME_CONNECTIONS_SEE` (filha de `ROLE_ACCESS_INTEGRATIONS`) **não** ganha
`PS_INTEGRATIONS_READ`, que mora na pai.

É por isso que o controller precisa de um **OR** entre as três permissões, e não de um AND nem de
um único check. A célula "SEE sem READ" é alcançável de verdade.

### Achado estrutural 2 — `EDIT sem SEE` é inalcançável via policy

A policy `PS_GAME_CONNECTIONS_EDIT` carrega **as duas** permissões (SEE e EDIT).
— `src/Migrations/Version20260806000000.php:63-76` (loop `foreach ([$editPermission, $seePermission] ...)`)

Consequência: por atribuição de policy, ninguém tem EDIT sem ter SEE. A combinação só existe por
atribuição direta de permissão — que é exatamente como o precedente de payment testa, mockando
`isGranted`:
— `tests/GatewayBundle/Controller/PaymentConfiguration/ProviderConfigurationControllerTest.php:430`

### Achado estrutural 3 — o owner se auto-sincroniza no login

`PasswordGrant` chama `OwnerPolicySynchronizer::syncMissingPolicies()` quando `$user->isOwner()`,
e o sincronizador atribui **todas** as policies existentes ao role.
— `src/OAuth2Bundle/Grant/PasswordGrant.php:74-76`
— `src/UserBundle/Service/OwnerPolicySynchronizer.php:17-41`

Consequência: o `INSERT INTO role_policy ... WHERE r.name = "owner"` da migration é cinto-e-suspensório,
não a fonte da verdade. Ainda assim mantemos, por consistência com CLS-1821 e para grants que não
passam pelo password grant.

---

## 3. Estado atual do código que o ticket toca

| Onde | Estado hoje | Fonte |
|---|---|---|
| Endpoint da lista | `GET /api/gateway/domain/{domainId}/integration/game-providers`, checa **só** `PS_INTEGRATIONS_READ` | `src/GatewayBundle/Controller/Integration/GameProviderController.php:21,42-46` |
| Resposta da lista | `id / name / type / status / createdAt / updatedAt` — **não existe `options`** | `src/GatewayBundle/Normalizer/Integration/GameProviderNormalizer.php:28-42` |
| Padrão a copiar | `FraudProviderController` com `READ_ROLES` + `isGrantedAny()` + `filterProviderSettings()` | **branch `origin/CLS-1871-CLS-2721`, não está em master** |
| Permissões SEE/EDIT | existem como linhas em `permission` desde CLS-1821, mas só a policy EDIT as carrega | `src/Migrations/Version20260806000000.php:19-23` |
| `PS_INTEGRATIONS_READ` | anexada à policy `ROLE_ACCESS_INTEGRATIONS` | `src/Migrations/Version20260901000000.php:13,37-45` |
| Tradução | `PS_GAME_CONNECTIONS_EDIT: 'Game connections'` — **sem** o verbo "Update" | `translations/messages.en.yml:1666` |
| Front — `canEdit` | `policies?.[ROLE_PAYMENT_PROVIDERS_EDIT]` para **todos** os grupos, não `false` | `celesta-backoffice-front/src/components/page-components/administration/integrations/detail/index.tsx:26` |
| Front — roles | `ROLE_GAME_CONNECTIONS_EDIT = "PS_GAME_CONNECTIONS_EDIT"` já existe; **não há** `..._SEE` | `celesta-backoffice-front/src/variables/roles.js:16`, `src/utils/policies.js:88,220` |

Nota: a branch de fraud (`CLS-1871-CLS-2721`) **não** adiciona migration nem tradução
(`git diff --stat origin/master...origin/CLS-1871-CLS-2721 -- src/Migrations translations/messages.en.yml` → vazio).
Ou seja: ela usa `PS_FRAUD_PREVENTION_CONNECTIONS_SEE` no controller, mas nenhuma policy concede
essa permissão isoladamente. **CLS-2980 é o primeiro ticket a criar uma policy de visualização
separada.** Fraud e various terão o mesmo buraco depois — fora do escopo, mas é dívida conhecida.

---

## 4. Matriz de variação (skill `ticket-matrix`)

### Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| D1 `PS_INTEGRATIONS_READ` | held / not held | `Version20260901000000.php:13` |
| D2 `PS_GAME_CONNECTIONS_SEE` | held / not held | `Version20260806000000.php:20` |
| D3 `PS_GAME_CONNECTIONS_EDIT` | held / not held | `Version20260806000000.php:20` |
| D4 Operação | GET list / UPDATE | `GameProviderController.php:42`; UPDATE = CLS-2979, rota ainda não existe |

**Descartadas como dimensão:**

- **Gateway type** — 19 valores em `GameGatewayConstants::TYPES`
  (`vendor/lancasters/constants/src/Game/GameGatewayConstants.php:27`). Nem o gate de role nem o
  `unset(...['options'])` ramificam por tipo: caminho único.
- **domainId** — a rota é domain-scoped mas a autorização não lê `$domainId`
  (`GameProviderController.php:44`).
- **status enabled/disabled** — o normalizer ramifica nisso (`GameProviderNormalizer.php:35`),
  mas é anterior ao ticket e ortogonal a permissão.
- **guards de existência de tabela na migration** — ambiente, não regra de negócio.

### Casos — GET list

R = `PS_INTEGRATIONS_READ`, S = `PS_GAME_CONNECTIONS_SEE`, E = `PS_GAME_CONNECTIONS_EDIT`

| # | Célula | Classe | Justificativa | Critério de aceite |
|---|---|---|---|---|
| 1 | – – – | **A** | — | dado token sem as 3, quando `GET /api/gateway/domain/{id}/integration/game-providers`, então `403` |
| 2 | R – – | **A** | — | então `200`, corpo é array e nenhum item tem a chave `options` |
| 3 | – S – | **A** | célula nova: hoje retorna `403` | então `200`, nenhum item tem `options` |
| 4 | R S – | E → 3 | mesmo short-circuit de `isGrantedAny()`, mesmo ramo falso do filtro de options | — |
| 5 | – – E | **A** | inalcançável por policy (achado 2), alcançável por permissão direta | então `200`, todo item tem `options` |
| 6 | R – E | E → 5 | mesmo par de ramos | — |
| 7 | – S E | **A** | única forma alcançável em produção de ter EDIT (policy "Update Game connections") | então `200`, todo item tem `options` |
| 8 | R S E | E → 7 | mesmo caminho; é o owner, já coberto por `testGetGameProvidersAction` | — |

### Casos — ESCRITA: UPDATE e CREATE (ambos no CLS-2979, ver D5 no `epic.md`)

O POST entrou no CLS-2979 por decisão do PO em 2026-09-21. Para permissão ele **não** acrescenta
célula: POST e PUT passam pelo mesmo `denyAccessUnlessGranted(EDIT)`, ramo único. As duas linhas
abaixo valem para os dois verbos.

| # | Célula | Classe | Justificativa | Critério de aceite |
|---|---|---|---|---|
| 9 | sem E (combos 1–4) | **A** (1 caso) | `denyAccessUnlessGranted(EDIT)` é ramo único; 2/3/4 E → 1 | dado token sem EDIT, quando UPDATE, então `403` e o registro fica inalterado |
| 10 | com E (combos 5–8) | **A** (1 caso) | idem; 6/7/8 E → 5 | dado token com EDIT, quando UPDATE, então `200` e o valor persiste |

16 células brutas — abaixo do limiar de ~20, então enumeração completa, sem pairwise.
Reduzidas por equivalência a **7 células A**.

### Casos — migration

| # | Célula | Classe | Critério de aceite |
|---|---|---|---|
| 11 | DB onde a permissão `PS_GAME_CONNECTIONS_SEE` já existe (criada pela 20260806) | **A** | `INSERT IGNORE` não duplica: `SELECT COUNT(*) FROM permission WHERE name='PS_GAME_CONNECTIONS_SEE'` = 1 |
| 12 | `down()` | **A** | remove a policy nova e seu `policy_permission`, **sem** apagar a linha de `permission` — ela pertence à 20260806 |
| 13 | owner recebe a policy nova | **A** | insert em `role_policy`; o auto-sync do login (achado 3) é backstop, não substituto |

**Armadilha da célula 12:** o `down()` da `Version20260806000000.php:184-188` faz
`DELETE FROM permission WHERE name IN (...)`. Copiar esse `down()` literalmente na migration nova
apagaria uma permissão criada por outra migration. O `down()` novo só pode mexer no que ele criou:
a policy `PS_GAME_CONNECTIONS_SEE` e seu vínculo em `policy_permission`.

### 4-bis. Variantes que a enumeração perdeu — review de 2026-09-22

Cada linha diz o que faltou e **por que** a enumeração não viu (fonte errada ou dimensão nunca
identificada). Detalhe e evidência em `../review-2026-09-22.md`.

| Variante | Onde ramifica | Por que escapou | Classe |
|---|---|---|---|
| `name` já existe no mesmo domínio (create e rename) | `GameGatewayConfiguration` `UniqueConstraint('name','domain_id')` — hoje termina em 500 | a enumeração leu forms e controller; nunca consultou os constraints da entidade/índices do banco | **A** — 400 no campo `name`, nada salvo |
| campo booleano **presente com `null`** | `Form::submit()` (false→null) + `BooleanTypeTransformer::reverseTransform(null)` → `false` | a dimensão "veio no payload" foi criada com dois valores (presente/ausente); JSON tem um terceiro | **A** — 400, registro inalterado |
| tipo de gateway × validator pinga ou não | `GameGatewayConfigurationValidator::GAME_LIST_METHODS` vs. primeiro call de cada `GameSynchronizer` | descartada como dimensão na matriz de permissão (correto lá); no 2979 o validator ramifica por tipo, e a enumeração usou nomes de método em vez dos sincronizadores | **A** por grupo — evolution/git_slot_park/gamble_hub/aleaplay hoje **não** pingam |
| payload ecoa campos de leitura (`type` igual, `id`, `status`, `createdAt`, `updatedAt`) | `UpdateGameGatewayConfigurationType` (extra fields) | só "type diferente" foi enumerado | decidir: aceitar `type` igual ou documentar |
| resultado do provedor: ok / rejeita / inalcançável | `validate()` → `Throwable` | célula A sem nenhuma execução em nenhum ambiente (teste, coleção, dev) | **A** — só verificável em preprod com credencial real |
| sink de log fora da aplicação | nginx sidecar do game (`celesta-argocd/…/game.yaml:104`) loga `$request_body` e `$resp_body` | "log line" foi lido como log da aplicação | AC do épico violada em produção até o sidecar mudar |

---

## 5. Comparação com a descrição do ticket — o que diverge

**Confere, sem discussão:**

- As duas permissões existem desde CLS-1821 e nenhum endpoint as checa. ✔
- A listagem só checa `PS_INTEGRATIONS_READ` e não há policy de visualização. ✔
- Policy nova sob `ROLE_ACCESS_INTEGRATIONS`, só com o SEE, concedida ao owner. ✔
- Listagem aceitando `READ ∨ SEE ∨ EDIT`. ✔ — e aceitar o READ é **obrigatório**: sem isso, quem
  tem o crachá vê payment/fraud/various e toma 403 só no game.
- Modelo de produto fechado com Lucas: **duas policies bastam**. "Update Game connections" (SEE+EDIT)
  e "View Game connections" (só SEE). Credencial só existe para preencher o formulário de edição —
  nenhuma outra tela precisa dela. Preço aceito conscientemente: **não existe perfil "confere a
  credencial mas não mexe"**. Se pedirem, é ticket novo.
- `PS_INTEGRATIONS_READ` **não** deve ser apagada: não é do game, é o crachá das quatro seções, e
  payment já depende dela em produção. Dentro do game ela é redundante com o SEE de propósito —
  é o caminho "vejo as quatro seções em leitura" com um grant em vez de quatro.

**Ponto de atenção que erra fácil:** a policy nova **tem** que se chamar `PS_GAME_CONNECTIONS_SEE`,
idêntica à permissão. O front filtra por **nome de policy**, não de permissão
(`users.js:249` ← `UserNormalizer.php:183`). Qualquer outro nome: backend funciona, front cego.

**Divergências reais:**

1. **Rótulo "Update Game connections" não existe.** Hoje é `PS_GAME_CONNECTIONS_EDIT: 'Game connections'`
   (`translations/messages.en.yml:1666`), e é a única policy de game que existe — não há outro
   candidato a que o ticket pudesse estar se referindo. Payment e fraud seguem a mesma convenção
   sem verbo.
   **Recomendação:** renomear para "Update Game connections" junto com o ticket. Com duas policies
   de game, "Game connections" não diz qual é a de escrita — e o risco é operacional: alguém concede
   achando que é leitura e entrega direito de trocar credencial. Fraud e various vão precisar do
   mesmo par quando ganharem suas policies de visualização, então é a direção, não uma exceção.

2. **Front (`canEdit` hard-coded `false`).** Não existe em master: o `canEdit` está fixo na permissão
   **de payment**, valendo para os quatro grupos (`detail/index.tsx:26`). Além disso o front é do
   **CLS-2981**, de outra pessoa. **Fora do escopo do CLS-2980** — mas o gate errado atinge fraud e
   various também, e isso não tem ticket. Levar ao TL.

3. **AC do épico incompleta** (observação para o PO, não bloqueia). A AC do CLS-1872 descreve dois
   estados — "Access Integrations" e "Access Integrations + Update Game connections". Com a policy
   nova passam a ser **três**. Falta a linha do usuário que só tem "View Game connections".

---

## 6. Próximos passos

1. Respostas dos 3 bloqueios + sign-off do Lucas na classificação A/N/E.
2. `/spec` do celesta-backoffice — a matriz vira a seção de acceptance criteria.
   Atenção: o `/spec` aborta se a branch não for master/main ou houver alteração não commitada.
   celesta-backoffice está hoje em `CLS-1746-CLS-2008`.
3. `/plan`, depois `db-query`, depois `ticket-postman` — uma iteração por célula A.

Relacionado: [[cls1872-cls2980-gateway-endpoint]]

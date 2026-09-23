# CLS-1872 — Create and edit game gateway connections on Backoffice

Planejamento de épico. **Superficial de propósito**: aqui só entra o que nenhuma subtask
consegue guardar sozinha — ordem, dependências, recursos compartilhados e decisões transversais.
Detalhe de ticket mora em `CLS-29xx/`. Requisito que é de um ticket só **não** entra neste arquivo.

Última atualização: 2026-09-21.

---

## 1. O que o épico entrega

Game é a última categoria de Integrations sem caminho de escrita no Backoffice. Hoje um operador
vê quais gateways a marca tem e se estão ativos, mas qualquer credencial, URL ou opção é alterada
por engenharia direto na tabela `Game_gateway_configuration`.

Depois do épico: conectar uma marca a um gateway ou rotacionar uma credencial é feito no Backoffice,
em minutos, sem ciclo de desenvolvimento.

---

## 2. As quatro subtasks

| Ticket | Entrega | Repos | Dono |
|---|---|---|---|
| **CLS-2978** | GET passa a devolver `options` e `freeRoundsCancelable` | celesta-game, celesta-backoffice | Lucas — **PRs**: celesta-game#1413, celesta-backoffice#3189 |
| **CLS-2979** | `POST` + `PUT`, com validação por ping no provider | celesta-game, celesta-backoffice | Lucas — **PRs**: celesta-game#1414, celesta-backoffice#3191 |
| **CLS-2980** | Policy de visualização + gate de acesso da listagem | celesta-backoffice | Lucas — **PR aberto**: celesta-backoffice#3188, celesta-fixtures#289 |
| **CLS-2981** | Cards clicáveis, página de detalhe, editor de JSON, save | celesta-backoffice-front | outra pessoa |

---

## 3. Ordem e dependências

```
CLS-2980  ─────────────────────────────┐   independente: policy + gate de acesso
   (pode ir primeiro)                  │
                                       ▼
CLS-2978  ──► CLS-2979  ───────────► CLS-2981
 campos        PUT + validação        front consome os três
```

**CLS-2980 não depende de ninguém** — desde que a decisão D1 abaixo valha.
**CLS-2981 depende dos três** e é de outra pessoa: precisa dos campos (2978), do PUT (2979) e da
permissão concedível (2980).

---

## 4. Decisões transversais

### D1 — Quem filtra o `options`? **CLS-2978.**

As descrições se cruzam: a do CLS-2978 diz *"only include it when the caller has PS_GAME_CONNECTIONS_EDIT,
wired in CLS-2980"*; a do CLS-2980 diz *"options only with PS_GAME_CONNECTIONS_EDIT"*. Os dois parecem
reivindicar o mesmo `unset`.

**Resolução:** o CLS-2978 cria o campo **e** o filtro, porque não faz sentido introduzir uma credencial
na resposta sem a proteção no mesmo commit. O CLS-2980 entrega a **permissão concedível** (a policy) e
o **gate de acesso** da listagem.

Consequência prática: o CLS-2980 deixa de estar bloqueado e pode ir primeiro.

Qualquer ordem é segura, aliás — as duas falham fechado:
- 2978 antes de 2980: o filtro existe, mas só o owner tem a permissão → ninguém mais vê `options`.
- 2980 antes de 2978: o gate abre para o SEE, mas não há `options` na resposta para vazar.

### D2 — Quem põe o EDIT no PUT? **CLS-2979.**

Mesma sobreposição. A descrição do CLS-2979 já diz *"behind PS_GAME_CONNECTIONS_EDIT"*. O CLS-2980
não toca no endpoint de escrita; apenas registra a regra.

### D6 — Branches empilhadas, uma sobre a outra. (Lucas, 2026-09-21, revisto em 2026-09-22)

Cada ticket sai do master direto, não um em cima do outro. Motivo: um PR que carrega o diff do
ticket anterior é pior de revisar do que um PR que conflita. O conflito a gente resolve aqui.

Os três mexem no mesmo arquivo — `GameProviderController.php`: o 2980 troca a linha do gate, o 2978
adiciona o filtro de `options` dentro do mesmo método, o 2979 adiciona dois métodos novos. Conflito
de git, não acoplamento lógico: cada um funciona sozinho.

**Dívida de teste que isso cria, e que não pode se perder.** O caso "usuário com apenas
`PS_GAME_CONNECTIONS_SEE` recebe a lista **sem** `options`" precisa dos dois tickets ao mesmo tempo:
o gate vem do 2980, o `options` vem do 2978. Em branches separadas, nenhum dos dois consegue cobri-lo.

- O CLS-2980 cobre: SEE recebe `200` (sem afirmar nada sobre `options`).
- O CLS-2978 cobre: READ não recebe `options`, EDIT recebe.
- **Quem entrar em segundo adiciona o teste que cruza os dois**, na resolução do merge.

Cada PR deve dizer, na descrição, o que ficou de fora e qual irmão é o dono — senão o revisor
cobra o que não é daquele ticket.

**Revertido em 2026-09-22 (Lucas).** Branches independentes deixavam de fora o único caso que
importa: o merge de um irmão pode quebrar o outro **sem conflito de texto**. Aconteceu de verdade —
o master trouxe `DomainGameGatewayConfiguration::fromEntity()` com 8 parâmetros e a chamada de 6
argumentos do outro lado; o git juntou os dois em silêncio e todo POST/PUT passou a dar
`ArgumentCountError`. Um PR verde por ticket não prova nada sobre a soma deles.

Agora cada PR tem como base o anterior: 2980 ← 2978 ← 2979, nos dois repositórios. O revisor vê só
o diff do próprio ticket (o GitHub desconta a base), e o CI de cada um já roda sobre a soma dos
anteriores. A dívida de teste abaixo deixou de existir: o teste cruzado entrou no 2978, que já
enxerga o gate do 2980.

### D5 — A criação entra no CLS-2979, não vira subtask nova. (PO, 2026-09-21)

O CLS-2979 passa a entregar **PUT e POST**, nos dois lados:

- celesta-game: `POST /api/domain/{domainId}/game-gateways`
- celesta-backoffice: `POST api/gateway/domain/{domainId}/integration/game-providers`, atrás de
  `PS_GAME_CONNECTIONS_EDIT`, repassando os erros do Game sem alterar

Duas consequências que o Jira ainda não registra:

1. **O POST tem um campo a mais que o PUT: o tipo de gateway.** Na edição só `name`, `enabled`,
   `options` e `freeRoundsCancelable` são graváveis; na criação é preciso escolher qual provedor é.
2. **A tela de criação não está no CLS-2981.** O front só prevê listar e editar. Sem isso, o POST
   existe e ninguém consegue chamá-lo pelo Backoffice. Precisa entrar no 2981 ou virar ticket à parte.

Para as permissões isso não muda nada: POST e PUT passam pelo mesmo gate de escrita.

### D3 — Modelo de permissão: duas policies para game, mais o crachá compartilhado.

| Policy | Permissões que carrega | O que o usuário faz |
|---|---|---|
| **Update Game connections** (já existe) | SEE + EDIT | vê a lista, vê a credencial, altera |
| **View Game connections** (CLS-2980 cria) | só SEE | vê a lista, sem credencial, não altera |
| **Access integrations** (compartilhada) | `PS_INTEGRATIONS_READ` | vê as quatro seções, sem credencial |

A credencial só existe para preencher o formulário de edição — nenhuma outra tela precisa dela.

**Preço aceito conscientemente:** não existe perfil "confere a credencial mas não mexe". Quem precisar
conferir ganha o direito de trocar. Se pedirem, é ticket novo.

`PS_INTEGRATIONS_READ` **não** é do game e **não** deve ser apagada — payment depende dela em produção.
Dentro do game ela é redundante com o SEE de propósito: é o caminho "vejo as quatro seções em leitura"
com um grant em vez de quatro.

### D4 — Rótulo: **não** renomear o existente. (Lucas, 2026-09-21)

O CLS-2980 cita "Update Game connections" duas vezes, mas sempre se **referindo** à policy que já
existe. A única ação pedida é *"Add the translation in messages.en.yml"*, singular, logo após criar a
policy nova. Não há pedido de renomeação.

Então o ticket **só adiciona** "View Game connections". O rótulo atual da policy de escrita,
"Game connections", fica como está.

**Observação a reportar, não a corrigir:** a tela passa a mostrar "Game connections" (escrita) ao lado
de "View Game connections" (leitura). Um admin pode conceder a primeira achando que é a de ver. Se o
PO quiser resolver, é ticket próprio.

Regra aplicada: não mexer no que o ticket não pede, mesmo quando a mudança parece inofensiva.

---

## 5. Recursos compartilhados — mexer aqui afeta as outras seções

| Recurso | Quem mais depende | Cuidado |
|---|---|---|
| tabelas `policy` / `permission` / `policy_permission` | payment, fraud, various | só inserir linhas; o `down()` só pode remover o que a própria migration criou |
| `PS_INTEGRATIONS_READ` | payment (em produção) | não renomear, não apagar |
| `translations/messages.en.yml` | as quatro seções | o CLS-2980 só **acrescenta** uma linha; nenhuma existente muda (D4) |
| nome da policy = nome da permissão | front | o front filtra por **nome de policy**, não de permissão. Nome diferente = backend funciona, front cego |

---

## 6. Divergências entre a AC do épico e as subtasks

Levantadas em 2026-09-21. As três primeiras são de produto e precisam do PO.

**A. ~~Não existe subtask de criação.~~ RESOLVIDO em 2026-09-21 — ver D5.**
A AC do ticket pai pede criação e nenhuma das quatro subtasks entregava. Levado ao Marcello (PO),
que confirmou ser oversight dele: *"Se não há, utiliza a CLS-2979 e adiciona o POST. Já temos o PUT."*
**Ponta solta:** a tela de criação continua fora do CLS-2981, e ele não se pronunciou sobre isso.

**B. O schema em `celesta-constants` foi abandonado.** A AC do épico pede um schema por gateway type
em `celesta-constants`, com o front montando o formulário a partir dele — e *"a field added to the
schema appears without a frontend release"*. As subtasks fazem outra coisa: o CLS-2981 usa um **editor
de JSON cru (CodeMirror)** e o CLS-2979 valida **construindo o client e pingando o provider**.

Isso invalida três ACs do épico: o formulário gerado, o campo novo sem release de front, e a mensagem
de erro **por campo** (o backend rejeita a configuração inteira, não campo a campo).

Não é necessariamente pior — validar contra o provider real pega erro que um schema não pega. Mas é
outra solução, e a AC precisa ser reescrita.

**C. A AC do épico só descreve dois estados de permissão.** "Access Integrations" e "Access Integrations
+ Update Game connections". Com a policy nova passam a ser três. Falta a linha do usuário que só tem
"View Game connections".

**D. `freeRoundsCancelable` não existe no épico.** Aparece nas três subtasks (2978, 2979, 2981) sem
estar em nenhum lugar da descrição do épico — inclusive com uma exigência de UX própria (aviso na
confirmação). Escopo introduzido no nível da subtask.

**E. O aviso genérico de edição sumiu.** A AC do épico pede confirmação avisando que a mudança afeta
todos os jogos daquele gateway para a marca. O CLS-2981 só prevê o aviso do `freeRoundsCancelable`.

---

## 7. Pontos abertos

**Para o PO**
- Divergências A, B, C, E acima.
- Desabilitar uma conexão tira os jogos do lobby? A AC do épico marca como suposição a confirmar com o Marcello.
- O épico registra um *"Compendium conflict"* sobre expor credenciais em endpoints de listagem
  (CLS-1465 nunca expor × CLS-2441 omitir × CLS-1874 mascarar `***`). Resolvido para game seguindo
  CLS-2441 (omitir). Reconciliar as categorias continua sendo ticket à parte.

**Para o TL**
- O `canEdit` do front aponta hoje para a permissão de **payment** e vale para os quatro grupos. O
  CLS-2981 provavelmente conserta só a parte de game; fraud e various ficam quebrados e sem ticket.
- O `FraudProviderController`, que o CLS-2980 manda usar como padrão, está na branch
  `CLS-1871-CLS-2721` e ainda não entrou em master.

**Risco técnico a verificar no CLS-2979**
- O PUT devolve *"Game's errors unchanged"*, e a validação **pinga o provider**. Um erro do provider
  pode ecoar a credencial enviada. A AC do épico exige que valor de `options` não apareça em nenhuma
  linha de log nem mensagem de erro.

**Decisão de daily, 2026-09-21**
- Existe um endpoint novo e um antigo no `celesta-gateway` para esse fluxo. **Usar o antigo**, alinhar
  com o time de front. Quais são exatamente, ainda não foi verificado em código.

---

## 8. Como este documento se relaciona com spec e plan

Isto **não** é spec. Quando cada ticket for começar, a spec e o plan nascem na branch daquele serviço,
pelos `/spec` e `/plan` do próprio repositório. A pasta da subtask é rascunho com prazo: vale até a
branch existir; depois o conteúdo migra para `_specs/` e sobra um ponteiro.

---

## 9. Estado da entrega (2026-09-21)

| Ticket | PRs | Verificado |
|---|---|---|
| CLS-2980 | celesta-backoffice#3188 · celesta-fixtures#289 | suíte 2971, migration do zero e rollback |
| CLS-2978 | celesta-game#1413 · celesta-backoffice#3189 | suítes 1245 e 2970 |
| CLS-2979 | celesta-game#1414 · celesta-backoffice#3191 | suítes 1252 e 2972 |
| CLS-2981 | — | outra pessoa |

### Branches locais de integração (não pushar)

`CLS-1872-integration` em celesta-game e em celesta-backoffice, com os três tickets mesclados.
Resultado: celesta-game 1252 testes, celesta-backoffice 2981 testes, zero falhas.

**Dois conflitos que só a branch combinada revelou:**

1. **celesta-game, conflito silencioso.** `DomainGameGatewayConfiguration::fromEntity()`, criado pelo
   CLS-2979, não passava os argumentos `options` e `freeRoundsCancelable` que o CLS-2978 acrescentou
   ao construtor. O git mesclou os dois lados **sem marcar conflito** e produziu um
   `ArgumentCountError` que nenhuma das duas suítes conseguiria pegar sozinha. É o caso que justifica
   a branch combinada existir.

2. **celesta-backoffice, conflito normal.** Os três tickets mexem em `GameProviderController.php` e no
   seu teste, como previsto em D6. Resolução mecânica: o gate de três permissões do 2980, o filtro de
   `options` do 2978 e os dois endpoints de escrita do 2979 coexistem sem se anular.

### A dívida de teste de D6 foi paga na branch combinada

`testGetGameProvidersOmitsOptionsForSeeOnlyCaller` — um chamador apenas com `PS_GAME_CONNECTIONS_SEE`
recebe a lista **sem** `options`. Precisa do gate do 2980 e do campo do 2978 ao mesmo tempo.
**Quem entrar em segundo leva esse teste para o seu PR.**

### Gotchas de ambiente encontrados no caminho

- celesta-game não tinha `.env` (gitignored, nenhum script cria); sem ele o phpunit não sobe.
- O cache de teste do celesta-game precisa ser apagado à mão (`var/cache/test`, `var/cache/testDebug`)
  quando se adiciona rota ou serviço — `cache:clear --env=test` não cobre o container usado pelo phpunit.
- `make test` do celesta-backoffice recria o banco sem carregar fixtures; todo teste funcional com
  token dá 401 até rodar `hautelook:fixtures:load --no-interaction --no-bundles --env=test`.
- O hook de commit rejeita a mensagem padrão de merge do git: precisa do prefixo (`CLS-1872 Merge ...`).

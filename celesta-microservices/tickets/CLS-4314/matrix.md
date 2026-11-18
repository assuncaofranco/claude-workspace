# CLS-4314 — matriz de variantes

Mudança: promotion ganha `POST /api/domain/{domainId}/rewarding` que recebe **pares** `{transactionId, playerId}`
(até 1000) e `event`; uma query por ids, e o service descarta a linha cuja promoção não é do jogador do par.
BO troca o loop por jogador por uma chamada por chunk de 1000 pares (`transaction_id`, `customer_id`) e remove
`PromotionClient::getRewarding`. Resposta da rota nova = `RewardingEntry`, igual à antiga.
(Revisto na terceira verificação, ver abaixo: ids soltos mudariam a resposta no RAF.)
Caminho único: o service passa a receber pares; a rota antiga converte `(playerId, ids)` em pares com o mesmo
jogador e chama o mesmo service. A query seleciona `p.playerId` e o filtro por par roda logo depois dela, antes de
carregar bônus e eventos (`RewardingService.php:95-97`). Confirmado que o RAF grava pelo handler Standard:
`HandlerFactory::get()` cai no `TYPE_STANDARD` quando o tipo não tem handler próprio (`HandlerFactory.php:32-34`).
Fontes lidas em `origin/master`, 2026-10-30. **Classificação assinada pelo Lucas em 2026-10-30.**

Sign-off:
- 10 (N): fica N. Princípio do expedite: **nada muda na resposta do BO**. É urgência de prod, não feature.
- 15 (N): a rota nova aceita `bet`, sem restringir.
- 16 (N): sem guarda de `null` no BO.
- E (3, 4, 6, 7, 17): um teste só, com todas as linhas misturadas na página do caso 2. O 14 fica coberto pelo teste do 13.

Critério transversal, derivado do princípio: para a mesma página, a resposta do transaction report na branch
é idêntica à do master (mesmos campos e valores, incluindo `rewarding`). Rodar a página do caso 2 contra os dois
e comparar. Duas precisões (2026-10-30, segunda verificação):
- comparar `rewarding` de cada transação **como conjunto**: `findRewardingRows` não tem `ORDER BY`
  (`PromotionRepository.php:207-235`), então a ordem entre promoções da mesma transação não é garantida nem no
  master. Não acrescentar `ORDER BY` no expedite;
- em preprod só roda uma versão por vez (`reference_preprod_branch_deploy`): **capturar a página no master antes
  de subir a branch**, com filtro de datas fixo no passado, para a página não mudar entre as duas capturas.

O front da Celesta não lê `rewarding` no relatório de transações (`celesta-backoffice-front` `origin/master`,
nenhuma branch remota, 2026-10-30). **Isso não significa que o campo não tem consumidor:** ele nasceu do CLS-594
(Story "Know which bets triggered the rewards", In prod), que pede a informação na API (*"/payment/transactions
should have related promotion/reward information"*, CLS-1211 "Make all the endpoints available in Gateway and
Backoffice"). O ticket do front (CLS-967) não inclui o relatório. O consumidor previsto é a API, e o "let the
operator assemble the display" do CLS-4314 aponta para o operador consumindo a API direto. Logo: o campo fica,
e não vai para a spec como "campo que ninguém vê".

Células que chamam a promotion direto (11, 13) não têm entrada pública em preprod: rodam no local e no proteus,
como a 12. Em preprod o que se observa é só o relatório do BO (1, 2, 8, 18) e a trace.

**Terceira verificação (2026-10-30): o filtro de jogador não era redundante.** O refer-a-friend grava o
`deposit_success` do indicado com o mesmo `transactionId` em duas promoções, a do indicado e a de quem indicou
(`ReferAFriend::dispatchRecord`, `ReferAFriend.php:201-217`; único override de `dispatchRecord`, o default em
`Standard.php:134` grava só no próprio jogador; o handler escreve `deposit`/`deposit_success`,
`Standard/Handler/RecordHandler.php:42-48`). Com `p.playerId = depositante`, a query devolve uma linha; sem o
filtro, duas, e o `rewarding` do depósito do indicado ganharia a promoção do indicante. Por isso a rota nova
recebe pares e filtra por par, reproduzindo exatamente a semântica de hoje em lote. Alternativa descartada:
devolver `playerId` na resposta e filtrar no BO, porque exige um segundo schema de resposta (o `RewardingEntry`
é compartilhado com a rota antiga, e o proteus valida a forma).
Por que a enumeração perdeu: a dimensão "rewarding por transação" contava **quantas** promoções, não **de quem**.

## Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| Tipo do movimento | deposit, deposit_first, deposit_second, withdraw, adjustment, refund | `celesta-constants` `TransactionMovementConstants::TYPES`; filtro em BO `TransactionReportController.php:92-95` |
| Jogadores distintos com depósito na página | 0, 1, ≥2 | agrupamento BO `TransactionReportController.php:97-100` (é o que sai) |
| Quantidade de ids elegíveis | 1, 1000 (máx.), >1000 | BO `Query.php:25` (`limit` máx. 1000); promotion `RewardingList.php:17,31` |
| Rewarding por transação | nenhum, 1 promoção, ≥2 promoções | promotion `PromotionRepository.php:223-225` (group by tx × promoção); merge BO `:123-127` |
| Status da promoção | engaged, expired, rewarded | `celesta-constants` `PromotionConstants::STATUSES`; uso em `PotentialWinningsCalculator.php:36` |
| Domínio da transação × domínio pedido | igual, outro | promotion `PromotionRepository.php:220` (`pc.domainId`) |
| Resposta da promotion | 200, falha (5xx, timeout 25s, 404 antes do deploy) | BO `catch (V2Exception)` `TransactionReportController.php:112-121` |
| Rota da promotion | nova (domínio), antiga (jogador) | promotion `RewardingController.php:46-51`; callers: gateway `PaymentTransactionController.php:143`, sportsbetting `promotion.go:103`, proteus `serviceAPI.ts:727` |
| `event` na rota nova | deposit, bet | `celesta-constants` `PromotionEventConstants::EVENT_TYPES`; validação `RewardingList.php` |
| Dono da promoção × depositante | mesmo jogador, outro jogador (RAF: indicante) | `ReferAFriend.php:201-217` (`dispatchRecord` grava na promoção do indicante); único override, default `Standard.php:134` |

## Casos

| # | Célula | Classe | Justificativa | Critério de aceitação |
|---|---|---|---|---|
| 1 | página só com withdraw/adjustment/refund (0 elegíveis) | A | o loop novo não pode mandar lista vazia: a promotion responde 400 (`Count(min: 1)`, `RewardingList.php:31`) e o BO logaria erro | dada uma página sem depósitos, quando o operador lista o transaction report, então a resposta é 200, todo `rewarding` é `null` e a promotion não recebe nenhuma chamada (preprod: nenhum span da promotion na trace; local: access log) |
| 2 | ≥2 jogadores × deposit × 1 promoção cada, mais um depósito sem promoção e um withdraw | A | núcleo do ticket: hoje N chamadas, depois 1; cada rewarding tem que cair na transação certa sem o filtro de jogador | dada uma página com depósitos de jogadores diferentes, quando o operador lista, então a promotion recebe **uma** chamada (preprod: um span da promotion na trace; local: access log); cada depósito com promoção traz `rewarding = [{promotionConfigurationId, rewards}]` da própria transação; o depósito sem promoção e o withdraw trazem `rewarding = null` |
| 3 | 1 jogador × deposit × 1 promoção | E → 2 | mesmo caminho: `array_chunk` + 1 chamada + merge `:123-127`; jogador único não ramifica mais nada depois da mudança | — |
| 4 | deposit_first, deposit_second | E → 2 | mesmo filtro `REWARDING_ELIGIBLE_TYPES` (`:26-30`) e mesma chamada com `EVENT_DEPOSIT` | — |
| 5 | withdraw, adjustment, refund em página mista | N | excluídos pelo filtro `:92-95` antes de qualquer chamada; coberto como linha de controle no caso 2 | — |
| 6 | depósito × ≥2 promoções | E → 2 | merge do BO acumula em array (`:124`), query agrupa por tx × promoção (`:223-225`); nenhum dos dois muda | — |
| 7 | depósito com status failure/pending | E → 2 (sem promoção) | a promotion só devolve evento `deposit_success` (`PromotionEvent::REWARDING_EVENT_NAMES_BY_TYPE`); cai em `rewarding = null` igual ao depósito sem promoção | — |
| 8 | página cheia: 1000 depósitos elegíveis | A | fronteira do limite da promotion e do timeout de 25s numa chamada só | dada uma página com 1000 depósitos, quando o operador lista, então a resposta é 200 dentro de 25s, com uma chamada à promotion e os rewardings preenchidos |
| 9 | >1000 ids elegíveis | N | impossível: `limit` máx. 1000 (`Query.php:25`); o chunk fica só como guarda | — |
| 10 | status engaged / expired / rewarded | N | três fatos: (a) a query não filtra por `p.status` (`PromotionRepository.php:207-225`); (b) os ids de bônus vêm de `findIdsGroupedByPromotionId` sem olhar status (`RewardingService.php:96,106`); (c) status só decide `potentialWinnings` (`PotentialWinningsCalculator.php:36`), que o BO descarta (`:124-127` copia só `promotionConfigurationId` e `rewards`) | — |
| 11 | rota nova × transação de outro domínio | A | sem o filtro de jogador, `pc.domainId` (`:220`) vira a única barreira entre clientes; ids são globais (payment auto-increment). **Só local/proteus** | dado um depósito com promoção no domínio 2, quando a rota nova do domínio 1 é chamada com o id dele, então a resposta é `[]` |
| 12 | promotion falha (5xx, timeout, 404) | A | muda o comportamento: hoje perde-se só um jogador, depois a página inteira. **Só local** (promotion parada no docker): 5xx/timeout não se provocam em preprod, e com promotion deployada antes o 404 não ocorre | dada a promotion indisponível, quando o operador lista, então a resposta é 200, todo `rewarding` é `null` e há um único log de erro com domainId e os ids |
| 13 | rota antiga × transação de outro jogador | A | o `playerId` opcional passa pelo mesmo service/query que gateway e sportsbetting usam. O proteus atual (`rewarding.pcpr-17.test.ts:247-257`) só cobre o mesmo jogador com lista não vazia, **não** este filtro. **Só local/proteus** | dado um depósito com promoção do jogador B, quando a rota antiga é chamada com o jogador A e esse id, então a resposta é `[]`; com o jogador B, traz o rewarding |
| 14 | rota antiga via gateway e sportsbetting | E → 13 | mesmo `RewardingController::listRewarding` → `getRewardingForTransactions` com `playerId` inteiro (rota exige `\d+`) | — |
| 15 | rota nova × `event = bet` | N | nenhum caller manda bet na rota nova; o BO fixa `EVENT_DEPOSIT` (`:110`). A validação aceita, e o filtro `eventType` separa os espaços de id | — |
| 16 | movimento elegível com `transaction_id = null` | N | a coluna é nullable (statistics `TransactionMovement.php:121`) e um `null` no lote dá 400 na promotion (`Assert\All Type integer`, `RewardingList.php:32-35`); mas o sync preenche `transaction_id = t.id` do payment em todo movimento de pagamento (`TransactionMovementManager.php:66,334`), e só adjustment fica sem, já filtrado em `:92-95` | — |
| 17 | promoção presente com `rewards = []` (engaged sem bônus, reward que falhou) | E → 2 | default `[]` em `RewardingService.php:106`; o BO copia como veio (`:124-127`). A coleção do caso 2 não pode assumir `rewards` cheio | — |
| 18 | depósito do indicado num RAF engaged, com a promoção do indicante gravada com o mesmo id | A | é a célula que prova o princípio: sem filtro por par, o `rewarding` ganharia a promoção do indicante. Local com fixtures; em preprod, procurar um par RAF com depósito já existente (leitura) antes de criar um | dado um depósito do indicado com `deposit_success` gravado nas promoções do indicado e do indicante, quando o operador lista a página com esse depósito, então `rewarding` traz **só** a promoção do indicado, idêntico ao master |
| 19 | rota nova × par (id do depósito do indicado, playerId do indicante) | N | nenhum caller monta esse par; o BO usa sempre o `customer_id` do movimento. A rota devolveria a promoção do indicante, que é o pedido | — |

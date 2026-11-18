# CLS-3282-CLS-4163 — matriz

Status: **assinada pelo Lucas em 2026-10-28.** Linhas citadas em `origin/master` de 2026-10-28.
Decisões de desenho: `memory/tasks/CLS-4163/decisions.md`.

Os endpoints de motivo ainda não existem; para eles a fonte dos valores é o texto do pai (CLS-3282) e do
4163. Para o gift, é o código atual.

## Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| `reasonId` no offer gift | ausente/null, inexistente, apagado, de outra marca, ativo da marca | 4163 item 7; pai AC "rejects an unknown, deleted or other-brand reason id", "can still be offered without a reason"; promotion `GiftController.php:94-101` (POST único, marca vem do path `:28`) |
| `reason` legado na requisição | ausente, null, texto | BO `GiftNormalizer.php:33` sempre manda a chave; promotion `GiftType.php:33-38` sem `allow_extra_fields` |
| Replay de idempotência | chave nova, chave já usada | promotion `GiftController.php:108-115` devolve o gift existente **antes** do form |
| Origem do offer | operador do BO (`sourceUserId`), cenário (`sourceScenarioId`) | promotion `GiftType.php:22-23`; o cenário não manda motivo hoje |
| Listar × paginação | com `limit`/`offset`, sem | convenção das listas da promotion: `Gift/QueryType.php:12-13`; o pai não fala em paginação e o front filtra apagadas do lado dele |
| `name` no criar | `""`, só espaços, 1..64, 65, duplicado ativo mesma grafia, duplicado ativo outra grafia, igual a um apagado, igual a um de outra marca | pai AC "Empty reason, or a duplicate of another non-deleted reason of the same brand (case-insensitive)", "Re-adding a deleted reason's name creates a new reason"; pai escopo `varchar 64` |
| Alvo do apagar | ativo da marca, já apagado, de outra marca, inexistente | 4163 item 4 (só "soft-delete endpoint"); pai AC "Deleting a reason sets its deleted at" — os três últimos não estão especificados |
| Listar | marca com ativas e apagadas, outra marca, ordenação por campo × direção, sem parâmetro de ordenação | pai AC "returns every reason of the brand, including deleted ones", "sorts on every column (asc/desc); default sort is reason A→Z" |
| `gift.reason` existente na migration | `birthday`, `christmas`, `easter`, `valentines_day`, `other`, null, outro texto | front `src/variables/index.js:269` `GIFT_REASONS`; rótulos em inglês `src/translations/en.js:2114-2118` batem com os nomes do seed. "Outro texto" só via chamada direta: BO `OfferType.php:58-62` aceita qualquer texto até 64. Banco local sem gift; preprod não consultado |
| Marca na migration | tem `player`/`promotion_configuration`, só tem `gift`, nenhuma linha em lugar nenhum | `Player.php:49`, `PromotionConfiguration.php:42`, `Gift.php:39` |
| Lista de gifts | motivo ativo, motivo apagado, sem motivo, migrado, legado `other` | 4163 item 8; pai AC "still show that reason's name" |
| Janela de deploy | promotion nova × BO antigo | BO `GiftNormalizer.php:33,111` |

## Casos

| # | Célula | Classe | Justificativa | Critério de aceitação |
|---|---|---|---|---|
| 1 | offer × `reasonId` ativo da marca | **A** | — | dado um motivo ativo da marca, quando `POST /domain/{d}/player/{p}/gift` com `reasonId`, então 201, e `GET /domain/{d}/gifts` devolve o gift com `reasonId` e `reasonName` desse motivo |
| 2 | offer × sem `reasonId` | **A** | — | dado nenhum `reasonId` (ausente ou null), quando o POST, então 201 e o gift volta com `reasonId` e `reasonName` null |
| 3 | offer × `reasonId` inexistente | **A** | — | quando o POST com um id que não existe, então 400 com erro em `reasonId` e nenhum gift criado |
| 4 | offer × `reasonId` apagado | **A** | — | dado um motivo apagado da marca, quando o POST com o id dele, então 400 e nenhum gift criado |
| 5 | offer × `reasonId` de outra marca | **A** | — | dado um motivo ativo da marca B, quando o POST na marca A com o id dele, então 400 e nenhum gift criado |
| 6 | offer × `reason` legado com texto ou null | **A** (compat) | é o que o BO atual manda (`GiftNormalizer.php:33`) | quando o POST com `reason: "birthday"` ou `reason: null` e sem `reasonId`, então 201 e o gift sem motivo; o texto não é gravado |
| 7 | offer × `reason` legado + `reasonId` | E → 1 | `reason` não mapeado, o caminho é o do `reasonId` | — |
| 8 | offer × replay de chave já usada, motivo apagado depois | **A** | `GiftController.php:108-115` devolve o gift original antes de validar; com Gedmo, a busca precisa desligar o filtro e trazer o motivo no join, senão `EntityNotFoundException` | dado um gift oferecido com motivo X e X apagado depois, quando o POST com a mesma chave de idempotência, então 200 com o gift original e `reasonName` de X |
| 9 | criar × nome válido | **A** | — | quando `POST` de motivo com `name: "VIP anniversary"`, então 201 e o motivo aparece na lista da marca com `deletedAt` null |
| 10 | criar × `""` | **A** | — | quando o POST com nome vazio, então 400 e nada salvo |
| 11 | criar × só espaços | E → 10 | o `TextType` do Symfony tem `trim: true` por padrão; `"   "` chega vazio | — |
| 12 | criar × 64 / 65 caracteres | **A** | limite da coluna | 64 → 201; 65 → 400 e nada salvo |
| 13 | criar × duplicado ativo, mesma grafia | **A** | — | dado "Birthday" ativo na marca, quando POST "Birthday", então 400 e nada salvo |
| 14 | criar × duplicado ativo, outra grafia | **A** | — | dado "Birthday" ativo, quando POST "birthday", então 400 |
| 15 | criar × igual a um apagado | **A** | — | dado "Birthday" apagado, quando POST "Birthday", então 201 com id novo; gifts antigos seguem com o id velho |
| 16 | criar × igual a um de outra marca | **A** | — | dado "Birthday" ativo na marca B, quando POST "Birthday" na marca A, então 201 |
| 17 | apagar × ativo da marca | **A** | — | quando o DELETE, então a lista devolve o motivo com `deletedAt` preenchido |
| 18 | apagar × já apagado | **A** | — | dado um motivo apagado, quando o DELETE de novo, então 404 e `deletedAt` não muda |
| 19 | apagar × outra marca / inexistente | **A** | busca por id + marca, como `TagController.php:223` | quando o DELETE com id de outra marca ou inexistente, então 404 e nada muda |
| 20 | listar × marca com ativas e apagadas | **A** | — | dado um ativo e um apagado na marca, quando o GET, então os dois voltam, o apagado com `deletedAt` |
| 21 | listar × outra marca | **A** | — | dado um motivo na marca B, quando o GET na marca A, então ele não aparece |
| 22 | listar × ordenação por campo × direção | **A** | — | para cada campo (`id`, `name`, `createdAt`, `updatedAt`, `deletedAt`) e cada direção, a ordem devolvida bate |
| 23 | listar × sem parâmetro de ordenação | N | nenhuma lista da promotion tem ordem padrão (`RepositoryTrait.php:11`); o A→Z do pai é critério do front, que manda `order` | — |
| 24 | migration × marca com player ou configuration | **A** | — | depois da migration, a lista da marca tem Birthday, Christmas, Easter e Valentine's day |
| 25 | migration × marca que só tem gift | **A** | sem `gift` na união, o gift fica sem motivo em silêncio | idem 24 para essa marca |
| 26 | migration × marca sem nenhuma linha / criada depois | N | lista vazia é estado válido no pai ("If every reason is deleted, the dropdown is empty") | — |
| 27 | migration × gifts existentes, qualquer `reason` | **A** | pai: "We can delete the existing gift test data" (TBD com o Yannick resolvido); decisão do Lucas 2026-10-29, revendo a tradução por chave | depois da migration, nenhum gift anterior a ela existe |
| 28 | — | — | absorvido pelo 27 | — |
| 29 | lista de gifts × motivo apagado depois | **A** | — | dado um gift com motivo X, quando X é apagado, então o gift continua devolvendo `reasonName` de X |
| 30 | deploy × promotion nova, BO antigo | **A** (deploy) | BO lê `$gift['reason'] ?? null` (`GiftNormalizer.php:111`); front antigo mostra "-" quando `reason` falta (`GiftsListItem.js:12`) | offer pelo BO antigo segue com 201 (caso 6); a lista no BO antigo mostra "-" no motivo, sem erro |
| 31 | offer por cenário (`sourceScenarioId`), sem motivo | E → 2 | mesmo POST, mesmo form; o cenário não manda `reasonId` nem `reason` | — |
| 32 | listar × paginação | **A** | `limit`/`offset` opcionais (`RepositoryTrait.php:18-23`) | quando o GET sem `limit`, então todos os motivos da marca voltam |

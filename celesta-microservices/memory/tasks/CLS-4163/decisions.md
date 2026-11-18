---
name: cls4163-decisions
description: "CLS-3282-CLS-4163 (promotion, motivos de gift) — decisões de desenho e ordem de deploy acertadas em 2026-10-28, antes do sdd-plan"
metadata:
  node_type: memory
  type: project
  originSessionId: 831bafd1-67ef-47f1-bf15-3ce9d4e5441e
  modified: 2026-11-04T10:33:49.788Z
---

Pai CLS-3282, irmãos CLS-4164 (BO, B-Team) e CLS-4126 (front). Matriz em
`tickets/CLS-3282/CLS-4163/matrix.md`.

- Coluna do motivo: `name` (convenção do repo: `Tag`, `RewardConfiguration`, `Gift` usam `name`).
- Resposta do gift: chaves novas `reasonId` + `reasonName`; `reason` deixa de ser devolvido e nunca muda de tipo (BO lê `$gift['reason'] ?? null`).
- Motivo opcional no offer; inexistente, apagado ou de outra marca → 400.
- Duplicado só validado no código, com `UniqueEntity(fields: ['domainId', 'name'])` (padrão de BO/CRM); com o filtro do Gedmo ligado, ignora apagados, e a collation `utf8mb4_unicode_ci` ignora maiúscula. Sem unique no banco e sem lock. **Único desvio do padrão:** o unique de soft delete (`UniqueConstraint(domain_id, name, deleted_at)`, wallet `BonusModel`, promotion `RewardConfiguration`) não impede duplicado ativo porque NULL não colide.
- Soft delete com Gedmo `SoftDeleteable`, como `RewardConfiguration`. Onde o apagado precisa aparecer, desligar/religar o filtro e trazer o motivo no join (`addSelect`), como `BonusRepository.php:61-62,75`: listar motivos, listar gifts, `findOneByIdempotencyKey` do gift, vencedor da corrida (`GiftController.php:179`). Decisão revista em 2026-10-28: sem Gedmo seria um terceiro desvio; promotion e wallet mostram pai apagado desse jeito.
- Delete: 404 para já apagado, outra marca e inexistente. Lista: `QueryType` padrão, `limit`/`offset`/`order` opcionais, sem ordem padrão.
- `reason` legado: `mapped => false` (padrão em BO/CRM/wallet para campo fora da entidade).
- 4164 (B-Team): o gateway dos motivos não pode injetar `DEFAULT_LIMIT` como o `GiftNormalizer` faz.
- Seed na migration: marcas = `DISTINCT domain_id` de `player` ∪ `promotion_configuration` ∪ `gift`. Marca nova começa vazia.
- Gifts existentes: **apagados** na migration (revisto em 2026-10-29). O pai diz "We can delete the existing gift test data", resposta do Yannick ao TBD; com isso o AC "migrated gifts show the same label" fica vazio e o pai não precisa de correção. A tradução por chave era possível (as chaves batem com os nomes do seed), mas o Lucas preferiu seguir o pai. Chaves confirmadas no front: `src/variables/index.js:269` `GIFT_REASONS`; rótulos `en.js:2114-2118` batem com os nomes do seed. O front traduz o rótulo em 6 idiomas; depois da mudança o nome vem do banco num idioma só (pai: tradução fora do escopo; avisar o PO).
- Nomes (2026-10-29, `sdd-plan`): `RewardOfferingReason`, tabela `reward_offering_reason`, `GET /reward-offering-reasons`, `POST /reward-offering-reason` (201), `DELETE /reward-offering-reason/{id}` (204); `Gift::offeringReason` sobre `reason_id`. Proteus: atualiza `gift.pcpr-26` + spec novo de motivos; Postman sem request nova (motivos no plano do 4164); migration verificada à mão, local e preprod.
- **Seed saiu da migration (2026-11-03, review do Bohdan):** migration só muda schema, que é o costume do time. O seed virou SQL na DI (staging e prod pelo deployer, pp1-4 pelo Lucas; pp1 já tem do primeiro deploy), em `tickets/CLS-3282/CLS-4163/seed-reasons.sql`, idempotente por marca. O `DELETE FROM gift` ficou na migration: roda uma vez, antes de existir gift com motivo. Script no celesta-scripts descartado (pesado demais para isso). Reset de auto_increment/truncate recusado: `GiftEventJob` já mandou os ids ao statistics. `EntityType` recusado. `csrf_protection` e `getBlockPrefix` removidos do `RewardOfferingReasonType`. Commit `099a8f1fd`, 1606 phpunit + 1150 behat + coleção 1-6 verdes.
- **Merge do master (2026-11-04, `afbca3286` + `40a5f6722`):** o CLS-3544 trouxe dois gates de cobertura 100% (PHPUnit só, e PHPUnit+Behat). `GiftTest` apagado como no master (`Gift.php` fora da cobertura); `GiftControllerTest` do master ganhou `reasonId`/`reasonName`; validador do motivo ganhou os testes de guarda e `getTargets`. 5465/5465 e 9844/9844 local.
- Coluna `gift.reason` intacta na parte 1 (rollback da promotion); sem `old_`.
- Deploy parte 1: promotion → BO → front, cada um aceitando `reason` legado e ignorando. Parte 2: BO tira `reason`, depois promotion tira do form e da entidade e **renomeia** a coluna para `old_reason` (Notion "Old data cleanup policy": coluna/tabela nunca é dropada no deploy, o TL dropa os `old_` na limpeza mensal). A política não cobre linhas: o `DELETE FROM gift` da parte 1 fica (confirmado 2026-11-02).
- Gateway e job-library fora: sem gift no `celesta-gateway`, `GiftEventJob` não leva motivo.
- PR no Proteus junto da parte 1 (payload de gift tem `reason`).

**Estado 2026-10-30:** promotion pushada no PR #581 (plano, código, `627bc661b` com as duas emendas do plano); label `sdd-implement` posto. Proteus PR #720 (branch `CLS-4163`): tsc, lint e unit (261, 100%) verdes; suites não rodadas contra stack local; o pre-push não fez a QAA review (sem `claude` no PATH do shell). O corpo pede ao QA renomear o step do offer para `(201 Created)` no Qase e cadastrar o `pcpr-27`. O `gh` agora tem `read:packages`; o `npm install` do Proteus passa o token por linha de comando, nunca em `~/.npmrc`. Steps 1-2 verdes (phpunit 1603, behat 1139, sdd-reviewer No findings na rodada 2); 3-4 pulados por escolha. Proteus não compilado: o token do `gh` não tem `read:packages`, `npm install` dá 403. O `gift.pcpr-26` já estava vermelho no master desde o CLS-412-CLS-3230 (offer 201, corpo de erro com `code`): alinhado neste PR, step renomeado para `(201 Created)` (Qase precisa acompanhar). Emendas de plano pendentes: `config/services_test.yaml` em Modify; tirar o builder de Create.

**Estado 2026-11-02:** #581 aprovado e CI verde; Proteus #720 CI verde, aguardando QA. Campos Deployment/Rollback instructions do CLS-4163 preenchidos (Proteus → promotion → BO #3292; rollback inverso; front fora, é do CLS-4126); Release note vazio (só para release de biblioteca). Pai CLS-3282 com a ordem dos três (promotion → BO → front). **pp1 2026-11-02:** branch deployada, migration rodou 11:16; 15 marcas × 4 motivos, nenhuma marca de player/configuration/gift sem motivo; gifts antigos apagados; BO atual oferece (gift 27, player de teste 282570, domínio 56, `reason` null) e lista sem erro. Comentário para o Francisco postado (12 itens, 4 ✅ em pp1, 8 ❌ dependendo de 4164/4126); CLS-4163 em **To review** desde 2026-11-02.

**Why:** acertado entre Lucas, Opus e Fable antes da matriz; a fase de plano relê o Jira, não o chat.
**How to apply:** passar isso ao `sdd-plan` em termos neutros. Pendente: quem é dono da parte 2.

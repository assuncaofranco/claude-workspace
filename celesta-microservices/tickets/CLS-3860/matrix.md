# CLS-3860 — matriz

Escopo depois do understand (memória `tasks/CLS-3860/understand.md`): só o test-provider. Custom-attributes já está
em 100% com pcov (CLS-3894). Régua do time: pcov, 100% por linha.

**Revisão 2026-11-10 (escopo mudou):** os testes saíram do CI do bundle e foram para o game. Split em dois MS:
- bundle (CLS-3860): remove `src/Promotion/`, `services_promotion.yml`, os guards de promotion e o guard
  `class_exists(Game)`;
- game (sub-task nova): composer em `dev-CLS-3860`, testes em `tests/TestProviderBundle/`, `src/` do bundle no
  `<source>` do `phpunit.xml`, sob o gate 100 que o game já tem.

A versão anterior tinha a dimensão "evento de CI" do workflow novo do bundle; caiu, porque o workflow do game não
muda.

## Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| Host que carrega o bundle | game, promotion | `TestProviderExtension.php:19` (`class_exists(App\AppBundle\Entity\Game)`) e `:23` (`FreeRoundConfiguration`, só existe na promotion: `git cat-file -e`) |
| Ação de webhook | bet, win, rollback, getBalance, freeRoundWin | `WebhookController.php:33` (`requirements`) |
| Resultado da cobertura do game | 100%, abaixo de 100% | `celesta-game/.github/workflows/ci.yml:46` `TEST_COVERAGE_PERCENTAGE: 100`; fronteira |

## Casos

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 1 | host game, boot depois da remoção | A | os guards e o mapping Doctrine saem; no game o ramo promotion nunca rodou (`FreeRoundConfiguration` não existe no game) e o ramo game sempre rodou, então nada deveria mudar, e é isso que se prova | given o game com o bundle da branch, when sobe em test, then o container compila, `debug:router` lista `webhook_test_provider`, `test_provider_lobby`, `test_provider_launch`, `test_provider_play`, e `POST /webhook/test-provider/getBalance` responde igual ao bundle v1.6 |
| 2 | host promotion | N | nenhuma branch da promotion instala o bundle (scan de `composer.json` em todos os remotes); o código que atendia esse host é removido | — |
| 3 | game × bet / win / rollback / freeRoundWin | N | o ticket não toca `Handler/` nem `Controller/`; os testes cobrem, mas o comportamento não muda. Se o plano exigir refactor de testabilidade aí, refazer a matriz | — |
| 4 | game × getBalance | E → 1 | já é a requisição de prova do caso 1 | — |
| 5 | CI do game, cobertura 100% com o bundle incluído | A | o `src/` do bundle entra na conta do gate existente | given o PR do game com o bundle da branch, when o CI roda, then o check de cobertura passa em 100% contando `vendor/celesta/test-provider-bundle/src` |
| 6 | CI do game, uma linha do bundle sem teste | A | fronteira do gate | given uma linha do `src/` do bundle sem teste, when o CI do game roda, then o check de cobertura falha |

## Critério que não vem de célula

- `src/Promotion/`, `Resources/config/services_promotion.yml` e os guards `class_exists` em `TestProviderBundle.php`
  e `TestProviderExtension.php` não existem mais; `services.yml` carrega sempre.

## Sign-off

Primeira versão assinada por Lucas em 2026-11-10. Revisão (testes no game) assinada no mesmo dia.

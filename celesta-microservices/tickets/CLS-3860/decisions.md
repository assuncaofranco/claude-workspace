# CLS-3860 — rascunho para os planos

Fonte para as respostas em lote do sdd-plan, no formato do template (`sdd-plan/SKILL.md:184` e `:372-385`).
Inglês porque é artefato do time. Vale para os dois planos: bundle (CLS-3860) e game (sub-task nova).

Todas as linhas confirmadas pelo Lucas em 2026-11-10 (guard: "se instalar no futuro, adapta-se o bundle").

---

## Architecture & Design: key design decision

**The test-provider-bundle is tested from the celesta-game test suite, because the bundle cannot run without the
whole game.**

- It imports 38 classes from celesta-game (`App\AppBundle\...`, `App\ApiBundle\...`) and extends some of them
  (`ProviderFactory`, `WebhookManager`).
- Those classes depend on the game's `vendor/` and kernel. The bundle's `composer.json` requires only `php`,
  `ext-bcmath` and `ext-json`, so none of that exists in the bundle repository.
- A CI job in the bundle would need either hand-written stand-ins for those 38 classes, which go stale silently
  when the game changes, or a full install of the game inside the bundle's pipeline, duplicating the game's CI.
- The game already installs the bundle (`require-dev`, loaded in `dev` and `test` only), runs PHPUnit with pcov
  and gates coverage at 100%.

So the bundle's `src/` joins the game's coverage source and is held to the same gate, tested against the real
game. A bundle change is validated through a game branch that requires the bundle branch (`dev-<branch>`), the
flow already used for any unreleased library.

## Decisions

| Question | Decision | Decided by |
|---|---|---|
| Where do the bundle's tests run? | In the celesta-game suite, with the bundle's `src/` under the game's 100% coverage gate; no CI job in the bundle, because the bundle cannot run without the game (see Architecture & Design). Departs from the sub-task's "run the check in CI for both bundles". | Lucas |
| Do the test files live in the bundle or in the game? | In the game, under `tests/TestProviderBundle/`: the game is the only place that runs them, and keeping them in the bundle would require mapping its test namespace into `vendor/`. | Lucas |
| Branch or line coverage? | Line coverage at 100%: the tests run in the game suite, which measures with pcov, and pcov has no branch mode. Switching the game to xdebug would slow its whole suite, against CLS-3204's "keep pcov"; CLS-3853 (game) was closed on the same basis. Belongs on the parent: CLS-3597 still asks for branch mode. | Team (Rasoul, on CLS-3853) |
| What happens to `src/Promotion/`? | Removed, with `services_promotion.yml` and the promotion guards in `TestProviderBundle.php` and `TestProviderExtension.php`: no branch of celesta-promotion installs the bundle. | Lucas, agreed with Marcello |
| What happens to the `class_exists(Game)` guard? | Removed, `services.yml` always loads: the game is the only host, and the guard would let a misinstall boot with the bundle's services silently skipped. | Lucas |
| What about celesta-custom-attributes-bundle? | Out of scope: already at 100% with pcov and a CI gate since CLS-3894. | Lucas |

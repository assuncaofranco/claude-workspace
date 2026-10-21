# CLS-3150 — rascunhos para o Jira

Nada daqui foi escrito no Jira ainda.

## 1. Acréscimos na spec do CLS-1283 (pai, do Marcello)

Só acréscimos; nada do texto atual muda.

**Problem statement**, ao fim do primeiro parágrafo:

> Wallet, backoffice, gateway and cms-v2 also still carry the Flipper client they added only to read
> `move_bonus_to_promotion`. It is wired in and has no caller. Promotion and game already removed theirs.

**Scope / In scope**, novo bullet:

> * Wallet, backoffice, gateway, cms-v2: remove the Flipper client entirely: the client class or plugin,
>   its service or plugin registration, the `FLIPPER_DATABASE_URL` parameter and env entries, its test
>   doubles and its tests. No trace of Flipper remains in these services or in promotion, game, cms and contact.

**Scope / Out of scope**, novo bullet:

> * The Flipper store itself, its `flips` and `flip_actors` rows, and `FLIPPER_DATABASE_URL` in the
>   deployment manifests. Flipper consumers owned by other teams (backoffice-front, sportsbetting) stay.

**Acceptance Criteria**, novos bullets (casos A da matriz):

> * Wallet, backoffice, gateway and cms-v2 boot and serve requests with `FLIPPER_DATABASE_URL` still
>   set in their environment, and also without it.
> * Gateway's `WorkerStateIsolationTest` passes without the Flipper case.
> * `git grep -i flipper` over src, config, tests and env files of wallet, backoffice, gateway, cms-v2,
>   promotion, game, cms and contact returns nothing.
> * No player-facing flow changes: no service reads any Flipper flag before or after.

**Surfaces touched**, acréscimos:

> * celesta-wallet, celesta-backoffice, celesta-gateway: Flipper client, its wiring and env.
> * celesta-cms-v2: the `flipper` Strapi plugin and its config.

## 2. Sub-tasks (uma por repositório)

Padrão das irmãs: título `<ação> [repo]`, componente `D-Team`, campo **Github repository**
(`customfield_11435`) preenchido. Sem links Blocks: os quatro são independentes, nada chama o que o
outro remove.

### CLS-3150 (existente): renomear

- **Título:** `Remove Flipper client [wallet]`
- **Github repository:** `celesta-wallet`
- **Descrição:**
  - delete `src/Library/FlipperClient.php` and `tests/Library/FlipperClientTest.php`
  - drop the `App\Library\FlipperClient` service from `config/services.yaml`
  - drop `flipper_database_url` from `config/parameters.yaml`
  - drop `FLIPPER_DATABASE_URL` and its comments from `.env.dev` and `.env.test`

### Nova: `Remove Flipper client [backoffice]`

- **Github repository:** `celesta-backoffice`
- **Descrição:**
  - delete `src/Library/FlipperClient.php` and `tests/Library/FlipperClientTest.php`
  - drop the service from `config/services.yaml` and the parameter from `config/parameters.yaml` and `config/services_test.yaml`
  - drop `FLIPPER_DATABASE_URL` from `.env.dev` and `.env.test`

### Nova: `Remove Flipper client [gateway]`

- **Github repository:** `celesta-gateway`
- **Descrição:**
  - delete `src/Library/FlipperClient.php`, `tests/Library/FlipperClientTest.php`, `tests/Mock/FlipperClient.php`, `tests/Mock/FlipperClientStub.php`
  - drop the service from `config/services.yaml`, the stub override from `config/services_test.yaml`, the parameter from `config/parameters.yaml`
  - drop the `flipper connection` case from `tests/Library/RoadRunner/WorkerStateIsolationTest.php`
  - drop `FLIPPER_DATABASE_URL` from `.env.dev` and `.env.test`

### Nova: `Remove Flipper plugin [cms-v2]`

- **Github repository:** `celesta-cms-v2`
- **Descrição:**
  - delete `api/src/plugins/flipper` and `api/tests/unit/plugins/flipper`
  - delete `api/config/flipper.ts` and the `flipper` entry in `api/config/plugins.ts`
  - drop `FLIPPER_DATABASE_URL` from `api/.env.example`
  - drop the "never consults the flipper plugin" test in `bonusListResolver.test.ts`
  - regenerate `api/package-lock.json`

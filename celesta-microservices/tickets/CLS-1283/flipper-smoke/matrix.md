# CLS-1283 Flipper: matriz

Sign-off do Lucas: 2026-10-20. Os critérios estão na spec do CLS-1283, sem a tabela.

**Dimensões**

| Dimensão | Valores | Fonte |
|---|---|---|
| Serviço | wallet, backoffice, gateway, cms-v2, promotion, game, cms, contact | escopo (memória `our-services`); `git grep -i flipper origin/master` |
| Processo | HTTP (php-fpm na wallet, RoadRunner no BO e gateway, Strapi no cms-v2), consumer, console | `.rr.yaml` no BO e gateway; `docker-compose.*` |
| `FLIPPER_DATABASE_URL` no deploy | presente, ausente | `parameters.yaml`: sem default no gateway, `default::` na wallet e BO |

**Casos**

| # | Célula | Classe | Justificativa | Checagem |
|---|---|---|---|---|
| 1 | wallet × HTTP × env presente | A | sai service, parâmetro, env | folders 1 e 2 (wallet atrás do gateway e do BO) |
| 2 | backoffice × RoadRunner × env presente | A | idem; client tinha `ResetInterface` | folder 2 |
| 3 | gateway × RoadRunner × env presente | A | idem + mocks + `WorkerStateIsolationTest` | folder 1 |
| 4 | cms-v2 × Strapi × env presente | A | plugin, config, lockfile, `dist` velho | folder 3 |
| 5 | {1..4} × env ausente | A | estado depois que o DevOps tirar a env | coleção de novo sem a env |
| 6 | {wallet, BO, gateway} × consumer, console | E → 1/2/3 | mesmo container compilado; zero consumidores em `src/` | — |
| 7 | promotion, game, cms, contact | N | client já removido (`b0712a91f`, `c0b78d713`) ou nunca existiu | grep |
| 8 | rastro | A | escopo "sem rastro" | `git grep -i flipper` em src, config, tests e env |
| 9 | jogador × qualquer fluxo | N | nenhuma flag lida no master desde CLS-2847/2848/2850/2851/2852 | — |

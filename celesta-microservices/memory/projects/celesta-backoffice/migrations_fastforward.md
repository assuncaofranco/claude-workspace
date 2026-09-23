---
name: celesta-backoffice-dev-db-has-no-migrations
description: "celesta-backoffice: o banco de DEV é montado por doctrine:schema:update a partir das entidades, não por migrations — migration de dados só roda no banco de TESTE"
metadata: 
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-21T11:07:08.732Z
---

**O banco de dev do celesta-backoffice não roda migrations, por desenho.** Verificado em 2026-09-21:
`doctrine_migration_versions` **não existe**, `doctrine:migrations:status` mostra `Current: 0` e
`Available: 254`, e mesmo assim o schema está completo com 92 policies.

Motivo, no próprio repositório:

- `install.sh:112-120` monta o banco de dev (e o de teste) com
  `doctrine:schema:update --complete --force` — schema derivado das entidades.
- `Makefile:30` e `:45` (alvos `test` e `coverage`) rodam
  `doctrine:migrations:migrate --no-interaction --allow-no-migration --env=test`.

**Consequência prática que engana:** uma migration de **dados** (INSERT em `policy`, `permission`,
`role_policy`, etc.) nunca aparece no banco de dev, porque `schema:update` só mexe em estrutura.
Consultar o dev e não achar as linhas **não** significa que a migration está errada — significa que
ela nunca rodou ali.

**How to apply:** para verificar qualquer migration de dados, consultar o banco de **teste**:
```
docker exec backoffice.php php bin/console dbal:run-sql --env=test "<SELECT ...>"
```
E rodar `make test`, que migra o banco de teste antes dos testes. Não tentar migrar o banco de dev:
os 254 disponíveis incluem migrations de 2017 que não replayam.

Se algum dia for mesmo necessário migrar um banco existente que esteja parado num ponto antigo
(situação diferente desta), o caminho é marcar o intervalo histórico como aplicado e só então migrar:
```
php bin/console doctrine:migrations:version --add --range-from='App\Migrations\Version<primeira>' --range-to='App\Migrations\Version<última anterior à sua>' --no-interaction
php bin/console doctrine:migrations:migrate --no-interaction
```
Nomes totalmente qualificados (`App\Migrations\VersionXXXX`); nomes curtos são rejeitados em silêncio.

Convenção de nome de arquivo neste repositório: `VersionYYYYMMDD000000` — data escolhida à mão, não
timestamp de gerador. Todas as vizinhas recentes seguem isso (`Version20260911000000` é a última).

## `make test` recria o banco e NÃO carrega fixtures

`make test` (Makefile:28-31) faz drop + create + `doctrine:migrations:migrate --env=test` e vai
direto para o phpunit. Nenhum passo carrega fixtures. Resultado: todo teste funcional que precisa de
token falha com **401**, e parece bug do seu ticket quando não é.

Depois do `make test`, carregar as fixtures com as mesmas flags do `install.sh:126-127`:
```
docker compose -f docker-compose.dev.yml exec -T php bin/console hautelook:fixtures:load --no-interaction --no-bundles --env=test
```
e então rodar `bin/phpunit` direto. O comando é `hautelook:fixtures:load` — `h:d:f:l` (citado no
CLAUDE.md do repositório) não existe neste projeto.

Verificado em 2026-09-21: 2 testes de `GameProviderControllerTest` falhavam com 401 no master e na
branch; passaram os 9 depois de carregar as fixtures.

---
description: Query a service's database straight from its container — read-only, for discovering real ids and column names before building a test scenario, or verifying what a fix produced.
allowed-tools: Bash(docker exec:*)
---

# db-query

Read-only lookup into a service's database, from the host, without a DB client and without a database
credential — the connection used is the application's own.

Container names, cluster, namespaces and AWS profile per environment come from the project's context
table (for Celesta: `celesta-microservices/context.yaml`, plus the per-service notes in
`celesta-microservices/db-reference.md`).

```bash
docker exec <container> php bin/console dbal:run-sql "<SELECT ...>"
```

## Rules

- **Read-only. Never write through this.** If a scenario needs a row that doesn't exist, create it
  through the real flow — API, a real event, or a console command; see `ticket-test`. This command is
  for diagnosing what's missing and verifying what a fix produced, nothing else.
- **Always write the SQL on ONE line.** A multi-line string — a heredoc, or a quoted query that
  starts with a newline — makes the command return a bare `[OK] 0 rows affected.` instead of results.
  That looks exactly like "no rows matched", so it silently produces wrong conclusions. Verified: the
  same `information_schema` query returned nothing multi-line and full results single-line.
- **Never guess a column name.** Discover it first:
  ```sql
  SELECT GROUP_CONCAT(COLUMN_NAME) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '<table>'
  ```
- **Production never.** Only local and the shared pre-production environment, and only reads.

## Consultas que sempre servem

**Chaves estrangeiras de uma tabela** — resolve "a tabela X pode existir sem a Y?", que é o que decide
a ordem de uma migration: um `CREATE TABLE` com FK não roda antes do pai existir.

```sql
SELECT COLUMN_NAME, REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='<table>' AND REFERENCED_TABLE_NAME IS NOT NULL
```

## Ambiente compartilhado — dentro do pod

Mesma ideia, mesma regra de SQL numa linha só. O ambiente de pré-produção costuma ser um namespace de
um cluster; o `exec` no container da aplicação dá a mesma conexão, então continua **sem credencial de
banco** — nada de senha de RDS para guardar, nada que possa vazar num repositório.

```bash
export KUBECONFIG=<scratchpad>/kubeconfig-pp       # nunca o kubeconfig padrão
aws eks update-kubeconfig --profile <perfil> --region <região> \
  --name <cluster> --kubeconfig "$KUBECONFIG"

kubectl --kubeconfig "$KUBECONFIG" -n <namespace> get pods | grep <serviço>
kubectl --kubeconfig "$KUBECONFIG" -n <namespace> exec <pod> -c <container-php> -- \
  php bin/console dbal:run-sql "<SELECT ... numa linha só>"
```

- **Precisa de sessão AWS viva.** O MFA depende de um código do autenticador do usuário — não dá para
  rodar sozinho. `ExpiredToken` em qualquer comando significa pedir para ele renovar, não contornar.
- **O pod tem mais de um container.** Sem `-c` o kubectl cai no primeiro, que pode ser o nginx.
- **Namespace sempre explícito** em todo comando. O namespace é o ambiente; omiti-lo é como errar de
  ambiente por descuido.

**Por que isso importa:** um ambiente compartilhado é alterado à mão por muita gente, inclusive nas
tabelas de permissão. Boa parte do que parece bug de código é dado inconsistente — e pela API isso é
invisível.

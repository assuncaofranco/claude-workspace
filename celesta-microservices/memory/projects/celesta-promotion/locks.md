---
name: celesta-promotion-locks
description: "Os locks Symfony da promotion são cluster-wide (Redis/Valkey externo por ambiente), não por pod — vale confiar neles para serializar entre consumers"
metadata:
  node_type: memory
  type: project
  originSessionId: ce1ff9bf-ec84-4901-ba43-d9604fdb7cab
  modified: 2026-10-26T13:56:01.712Z
---

Os `LockFactory` da celesta-promotion usam `RedisStore` sobre `local_redis` (`config/services.yaml:71-74`,
decorado por `RetryTillSaveStore` 100ms × 3000). O host `LOCAL_REDIS_HOST` em todos os ambientes é um
Valkey externo por ambiente (`celesta-argocd-parameters/<env>/promotion/parameters.yaml:8`): prod-1
`celesta-prod-1-promotion.prod-1.octopoprod.com`, prod-2 `celesta-prod-2-valkey.prod-2.octopoprod.com`,
preprods `valkey*-celesta.preprod.octopodev.com`.

**Why:** o nome `local_redis` / `localredis.docker` no `.env` sugere Redis por pod, e isso levou o Opus a
questionar (2026-10-26, CLS-3676) se check-before-act dentro do lock bastava ou se precisava de unique no banco.

**How to apply:** lock por `transactionId` (deposit handlers) e por configuration
(`Standard\Handler\RewardHandler::acquireConfigLock`, TTL 40s) serializam entre pods. Checar antes de agir
dentro deles é seguro; não exigir unique só por desconfiança do lock. Verificado em [[cls3676-decisions]].

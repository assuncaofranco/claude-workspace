---
name: cls3542-contact-coverage-review
description: "Review 2026-10-23 do contact PR #428 (Bohdan, cobertura 100%) — o retry de 5xx do EDP é código morto em prod e o PR cobre com um Response fake"
metadata:
  node_type: memory
  type: project
  originSessionId: a92e894a-0b89-410c-b04e-35d8d1c932d9
  modified: 2026-10-23T07:52:45.498Z
---

contact PR #428, sub-task sem descrição (pai CLS-2947). Só testes + `.claude/rules` + `CLAUDE.md` + remoção do legado `_specs/_plans` do CLS-3290. Nenhum `src/` mudou.

- Local 2026-10-23: 44 testes verdes, 100% (470/470). O CI do contact só roda com APPROVED, então a branch não tinha rodado.
- **Achado principal:** `EDPClientProvider::send()` só trata 5xx (`>= RETRY_STATUS_CODE`) e faz retry depois que `sendApiRequest` retorna, mas o Guzzle usa `http_errors` true por padrão e lança no 5xx, que cai no catch e grava FAILURE com status 0. Resultado em prod: o EDP **nunca** faz retry, mesmo com `retry_send_count`. E `$response['errors']` num Response real daria fatal. O teste `EDPClientProviderServerErrorRetryTest` cobre isso com um Response anônimo que devolve 200 para quem chama do namespace do Guzzle (`debug_backtrace`) e implementa ArrayAccess. Os 100% dependem disso.
- O gate `TEST_COVERAGE_PERCENTAGE` continua 70 em `.github/workflows/ci.yml`; o pai pede subir.

**Why:** cobertura por fake esconde bug de produção atrás de um número verde.
**How to apply:** se esse PR voltar, conferir se o branch de 5xx foi corrigido (http_errors false + leitura do body) ou removido, e não só re-coberto.

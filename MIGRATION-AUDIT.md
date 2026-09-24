# Auditoria da migração

Origem: `/Users/l.franco/.claude-pre-git-2026-09-22` (104 arquivos)

| situação | n | significa |
|---|---|---|
| MODIFICADO | 18 | conteúdo mudou — **é aqui que um equívoco estaria** |
| VAULT | 4 | saiu para ~/.claude-secrets, ponteiro ficou |
| ABSORVIDO | 8 | conteúdo reescrito em rules/, original removido |
| DIVIDIDO | 5 | virou mais de um arquivo |
| IDÊNTICO | 67 | byte a byte igual — nada a conferir |
| NÃO MAPEADO | 2 | estado de runtime, nunca foi para o repositório |

## MODIFICADO

- `commands/db-query.md`
  → `global/skills/db-query.md` — 5205 -> 3546 bytes (-1659)
- `commands/oncall.md`
  → `global/skills/oncall.md` — 7088 -> 7494 bytes (+406)
- `commands/ticket-code.md`
  → `global/skills/ticket-code.md` — 5964 -> 4951 bytes (-1013)
- `memory/MEMORY.md`
  → `global/memory/MEMORY.md` — 148 -> 545 bytes (+397)
- `postman/CLS-1746-CLS-2008.preprod-1.postman_collection.json`
  → `celesta-microservices/postman/CLS-1746-CLS-2008.preprod-1.postman_collection.json` — 29047 -> 28654 bytes (-393)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/MEMORY.md`
  → `celesta-microservices/memory/MEMORY.md` — 9681 -> 8722 bytes (-959)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/project_spec_ownership_shift.md`
  → `celesta-microservices/memory/project_spec_ownership_shift.md` — 2046 -> 2029 bytes (-17)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/CLS-1872-CLS-2980/testing-specifics.md`
  → `celesta-microservices/memory/tasks/CLS-1872-CLS-2980/testing-specifics.md` — 9136 -> 9214 bytes (+78)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/CLS-1872/review-2026-09-22.md`
  → `celesta-microservices/memory/tasks/CLS-1872/review-2026-09-22.md` — 8031 -> 8070 bytes (+39)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_cel8373_change_password_confirmation_email.md`
  → `celesta-microservices/memory/tasks/project_cel8373_change_password_confirmation_email.md` — 5360 -> 5365 bytes (+5)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_cls1186_master_merge.md`
  → `celesta-microservices/memory/tasks/project_cls1186_master_merge.md` — 7278 -> 7238 bytes (-40)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_cls1186_preprod_newman.md`
  → `celesta-microservices/memory/tasks/project_cls1186_preprod_newman.md` — 2680 -> 2685 bytes (+5)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_cls1285_cls2391_review_decisions.md`
  → `celesta-microservices/memory/tasks/project_cls1285_cls2391_review_decisions.md` — 4313 -> 4286 bytes (-27)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_cls1843_cls1912_currency_nullable.md`
  → `celesta-microservices/memory/tasks/project_cls1843_cls1912_currency_nullable.md` — 5005 -> 4992 bytes (-13)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_cls2450_cls2452_duplicate_subbalance_investigation.md`
  → `celesta-microservices/memory/tasks/project_cls2450_cls2452_duplicate_subbalance_investigation.md` — 9318 -> 9291 bytes (-27)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/tasks/project_custom_attributes_reward_configuration.md`
  → `celesta-microservices/memory/tasks/project_custom_attributes_reward_configuration.md` — 4580 -> 4617 bytes (+37)
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/user_two_lucases.md`
  → `celesta-microservices/memory/user_two_lucases.md` — 1469 -> 1479 bytes (+10)
- `shared/coding-standards.md`
  → `celesta-microservices/shared/coding-standards.md` — 13923 -> 8556 bytes (-5367)

## VAULT

- `commands/preprod-test.md`
  → `credenciais -> ~/.claude-secrets/celesta-preprod.md; método reescrito genérico` — segredo fora da árvore do git
- `commands/ticket-postman.md`
  → `credenciais -> ~/.claude-secrets/celesta-dev.md; referência Celesta -> postman-reference.md` — segredo fora da árvore do git
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/project_game_nginx_body_capture.md`
  → `~/.claude-secrets/celesta-prod-findings.md (ponteiro ficou no repo)` — segredo fora da árvore do git
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/projects/celesta-cms-v2/preprod-1-test-admin.md`
  → `~/.claude-secrets/celesta-cms-v2.md (ponteiro ficou no repo)` — segredo fora da árvore do git

## ABSORVIDO

- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_ask_before_workaround_on_stack_problems.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_epic_planning_folder.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_local_postman_collections_folder.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_make_init_after_branch_switch.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_never_fix_outside_ticket_scope.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_review_product_impact_not_just_current_code.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_sdd_output_folder.md`
  → `global/rules/` — reescrito por tema, original removido
- `projects/-Users-l-franco-Desktop-celesta-projects/memory/preferences.md`
  → `global/rules/` — reescrito por tema, original removido

## DIVIDIDO

- `CLAUDE.md`
  → `dividido em global/CLAUDE.md + router.md + rules/ + overlay da Celesta`
- `RTK.md`
  → `global/RTK.md`
- `memory/celesta-infra.md`
  → `celesta-infra/memory/celesta-infra.md`
- `settings.json`
  → `celesta-microservices/settings/settings.json (26 entradas com credencial removidas)`
- `settings.local.json`
  → `celesta-microservices/settings/settings.local.json`

## IDÊNTICO (67)

Movidos sem alteração. Para conferir:

```bash
python3 global/scripts/audit-migration.py | grep MODIFICADO
```

---

## Ponto cego conhecido

Esta auditoria compara **só o que veio de `~/.claude/`** (104 arquivos), porque foi disso que se fez
cópia antes de mexer.

Duas pastas vieram de outro lugar, por `mv` e não `cp`, então não têm estado pré-migração no backup:

| pasta | de onde veio | onde está o original |
|---|---|---|
| `celesta-microservices/tickets/` | `~/Desktop/celesta-projects/tickets/` | conteúdo íntegro em `~/.claude-secrets/celesta-prod-log-capture-report.md` e `celesta-prod-findings.md` para os dois arquivos redigidos; o resto está idêntico no commit inicial |
| `celesta-microservices/postman/` | `~/Desktop/celesta-projects/_local-postman-collections/` | commit inicial, com as credenciais já esvaziadas |

Ou seja: nada se perdeu, mas para esses dois a prova está no vault e no commit inicial, não aqui.

## Como reproduzir

```bash
python3 global/scripts/audit-migration.py                    # relatório inteiro
python3 global/scripts/audit-migration.py | grep -A2 MODIFICADO
diff <(cat ~/.claude-pre-git-2026-09-22/commands/oncall.md) global/skills/oncall.md
```

O diretório pré-git é `~/.claude-pre-git-2026-09-22/` (`chmod 700` — contém credencial viva, por isso
nunca entra no repositório).

---
name: cls3507-numerical-ca-takeover
description: "CLS-3507 numerical custom attributes — Lucas assumed CLS-3793 (crm #2117) and CLS-3796 (BO #3283) from Pedro Martins on 2026-11-02; SDD review state and blockers"
metadata:
  node_type: memory
  type: project
  originSessionId: e370cba6-e856-408c-85b8-d2aa4dc31111
  modified: 2026-11-02T13:25:41.229Z
---

Lucas assumiu em 2026-11-02 os PRs do Pedro Martins (outro time; era para ser do D-Team):
crm #2117 (CLS-3793, empilhado em #2116 ← #2114, ambos CLS-3792) e BO #3283 (CLS-3796).
Para assinar: review + teste em PP.

**Bloqueio central:** CLS-3791 (custom-attributes-bundle, D-Team) está To Do, assignee Lucas,
sem branch nem PR (último tag v2.6). Validação 2.456/abc → 400, normalização 2.50 → 2.5, type
imutável no PUT, default não numérico e registro com abc moram no bundle. Também o bug do
`empty_data` (POST sem `type` → 400 na 2.6) que trava o #2116. Constants CLS-3790 = #617, aberto.

**Desvios de SDD achados:** branch `CLS-3507-<KEY>` em vez do key puro (o `sdd-implement`
recusa); label `sdd-plan` ausente nas duas sub-tasks; Postman (celesta-qaa-functional-tests)
sem branch para nenhuma; Proteus do BO (pcb-16) sem PR — o crm está no proteus #665 (Daniel,
SSD-758) + qaa-mock #252. Código dos dois diffs: sem bug encontrado.

**Atualização 2026-11-02:** o CLS-3791 virou nosso. O patch do Pedro foi aplicado com `git am` na branch
`CLS-3791`, criada a partir da `CLS-3894-development`, com a autoria dele mantida. O plano foi
reescrito no formato SDD e o PR é o bundle #50 contra `development`. A linha 2.x é a `development`
e a 1.x é o `master`. A label `sdd-plan` foi posta. Testes: 161 passando, 100%. Acordo de divisão:
nós instalamos no BO, o time C instala no crm (#2116/#2117) e o teste é em PP1, com o crm subindo
antes do BO. Antes da tag 2.7: mergear o #49 e o constants #617, e voltar o pin do constants pra caret.

**Why:** ticket herdado; o que falta é sobretudo o bundle, não os dois PRs.
**How to apply:** começar pelo CLS-3791 antes de mexer em #2117/#3283; ver [[project_stacked_pr_merge_trap]] para a pilha do crm.

---
name: epic-planning-folder
description: "Épico com várias subtasks ganha uma pasta de planejamento fora das branches, em ~/Desktop/celesta-projects/tickets/<épico>/, antes de qualquer /spec"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-21T09:03:13.075Z
---

Antes de rodar `/spec` de qualquer subtask de um épico multi-ticket, montar o planejamento em
`~/Desktop/celesta-projects/tickets/<épico>/`:

```
tickets/CLS-1872/
├── epic.md              ordem, dependências, decisões transversais, recursos compartilhados,
│                        divergências entre a AC do épico e as subtasks, pontos abertos
├── CLS-2978/description.md    descrição do Jira verbatim + rascunhos daquele ticket
├── CLS-2979/...
└── ...
```

**Why:** os problemas que mais custaram tempo no CLS-1872 eram todos *entre* tickets — a ordem de
dependência, quem implementa o filtro que dois tickets reivindicam, e a tabela de permissão
compartilhada com payment/fraud. Uma spec dentro da branch enxerga só o próprio ticket, então não
existe lugar para isso e a discussão se repete a cada subtask.

**How to apply:**
- O `epic.md` guarda **só** o que nenhuma subtask consegue guardar sozinha. Requisito de um ticket
  só não entra lá — vira duplicata que desatualiza.
- A pasta da subtask é rascunho com prazo: vale até a branch existir. Quando o `/spec` do serviço
  roda, o conteúdo migra para `_specs/` e sobra um ponteiro.
- Spec e plan continuam nascendo nas branches, pelos `/spec` e `/plan` do próprio repositório —
  isto não substitui o SDD, vem antes dele.
- Precedente da mesma forma: `~/Desktop/infra/tickets/`.

Relacionado: [[ticket-matrix]] (a matriz de um ticket nasce na pasta da subtask e migra para a spec).

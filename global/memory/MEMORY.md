# Memory Index (Global)

Memória que não depende de empresa nenhuma — como trabalhar, não sobre o quê. O contexto por projeto
vive na memória daquele projeto (`celesta-microservices/memory/`, `celesta-infra/memory/`), consultado
sob demanda, não pré-carregado aqui.

O fluxo de ticket em si não é memória: são as skills em `global/skills/` (`ticket-understand`,
`ticket-matrix`, `ticket-test`, `ticket-code`, `ticket-review`, `ticket-postman`, `preprod-test`,
`db-query`, `explain`). Alerta de produção tem skill própria, `oncall`, deliberadamente fora dessa
cadeia. O roteamento por atribuição (dev/review/teste → quais skills encadear) está em
`global/CLAUDE.md`.

- [Preferências](preferences.md) — comunicação terse/humana, opinião genuína em vez de carimbo,
  disciplina de review (verificar estado real do git, sinalizar marcas de IA) e citar o caminho do
  arquivo de padrões quando um review o invoca

## Feedback — como trabalhar, aprendido na prática

- [Nunca consertar fora do escopo do ticket](feedback/feedback_never_fix_outside_ticket_scope.md) —
  achar um defeito fora do escopo não autoriza corrigi-lo, nem depois de investigar; código tolerante
  costuma estar segurando dado sujo antigo, e endurecê-lo vira indisponibilidade
- [Perguntar antes de contornar problema de stack](feedback/feedback_ask_before_workaround_on_stack_problems.md) —
  quebra de ambiente vai para o usuário, nunca para um contorno; e seguir as flags do próprio
  install.sh/Makefile do repositório
- [Review com lente de impacto de produto](feedback/feedback_review_product_impact_not_just_current_code.md) —
  não descartar um comentário de review só porque é inócuo no código de hoje
- [`make init` depois de troca de branch](feedback/feedback_make_init_after_branch_switch.md) —
  cache e banco de teste velhos produzem erro que parece regressão
- [Planejamento de épico fora das branches](feedback/feedback_epic_planning_folder.md) — épico
  multi-ticket ganha pasta própria antes de qualquer `/spec`
- [Pasta local de coleções de Postman](feedback/feedback_local_postman_collections_folder.md) —
  coleção ad-hoc nunca dentro do repositório de um serviço
- [Pasta de saída do SDD](feedback/feedback_sdd_output_folder.md) — spec e plano fora da pasta de
  ferramentas; o layout é por serviço, não assumir um pelo outro

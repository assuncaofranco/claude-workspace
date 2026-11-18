# CLS-3507 — DI da nossa parte (CLS-3791 bundle, CLS-3796 BO), 2026-11-02

Gravado nos campos do CLS-3791 (DI, rollback, release note) e do CLS-3796 (DI, rollback), e na seção
"Post deployment" do bundle #50 e do BO #3283. O DI do épico inteiro já está no pai CLS-3507 (Pedro).

## Por quê

- **Bundle antes de tudo:** é biblioteca. O BO e o crm só mergeiam com a tag v2.7.0 no composer, que
  hoje aponta pra `dev-CLS-3791`. A tag sai da `development` (linha 2.x), depois do #49 (base da
  branch) e da tag do constants CLS-3790, porque o bundle não pode ser tagueado com dependência dev.
- **crm antes do BO, recomendado e não obrigatório.** Os estados intermediários:
  - BO novo com crm velho: `numerical` não funciona (o crm recusa ou ignora), mas ninguém manda
    `numerical` até o front CLS-3797 subir. Sem `type` continua igual a hoje.
  - crm novo com BO velho: o BO antigo não manda `type` e o bundle 2.7 cria `string` (fix do
    `empty_data`). `numerical` dá 400 no próprio BO.
- **Rollback do BO sozinho:** o BO não lê configuração pelo enum (plano do CLS-3796), então voltar só
  devolve o 400 em `numerical`.
- **Rollback do crm é do time C, e não tem volta** quando já existir uma configuração `numerical`:
  um crm sem o case dá 500 ao ler. A saída é corrigir pra frente.

## Pro Lucas, fora do que a gente escreve

- O DI do pai não cita o **CLS-3788** (scenario, Ready, sem código). O plano do CLS-3793 diz que o crm
  só sobe depois dele: o job do scenario compara o `value` da resposta do PATCH com a string que mandou,
  e com o bundle 2.7 um atributo numérico volta como número (`120` contra `"120"`). Só afeta atributo
  numérico, que não existe até alguém criar. É do time C, mas vale levantar.
- Também falta no pai mergear o #49 antes da tag do bundle.

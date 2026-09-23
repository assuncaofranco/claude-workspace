---
name: celesta-cms-v2-preprod-1-test-admin
description: "Existe um admin de Strapi criado à mão para celesta-cms-v2 (marca madnix) em preprod-1, para testar upload/S3 sem depender da conta de outra pessoa — a credencial vive em ~/.claude-secrets/celesta-cms-v2.md"
metadata:
  node_type: memory
  type: reference
  originSessionId: c737f90c-e477-433f-aa48-2a79b567a545
  modified: 2026-09-22T00:00:00.000Z
---

Existe uma conta de admin de teste para a instância Strapi do celesta-cms-v2 (madnix) em preprod-1.

**A credencial não está aqui.** Ela vive em `~/.claude-secrets/celesta-cms-v2.md`, fora da árvore do
git — este arquivo é versionado e uma senha nele seria uma senha publicada.

**Por que existe:** criada em 2026-09-03 durante o CLS-1396 (migração de upload para S3), porque
nenhuma credencial de admin de pp1 era conhecida. Criada por um Pod avulso rodando
`node commands/admin.js create-user` — mesmo mecanismo do `make create-owner` local, e não via
`kubectl exec` direto; ver [[celesta-cms-v2-strapi-dev-gotchas]] para o motivo.

**Como aplicar:** reaproveitar essa conta para teste manual contra cms-v2/madnix em preprod-1 em vez
de criar mais uma. Só pp1 — os outros ambientes não têm.

**Pendência:** a conta nunca entrou no cofre do time, embora Infisical e AWS Secrets Manager rodem no
cluster. Se o uso passar de ad-hoc, mover para um cofre de verdade ou revogar.

# Celesta Infra — overlay

Contexto da infraestrutura, separado dos microserviços porque é outro diretório de trabalho
(`~/Desktop/infra`), outro conjunto de repositórios e outro tipo de risco.

O método genérico está em [`../global/CLAUDE.md`](../global/CLAUDE.md). A memória do domínio —
repositórios, ambientes, Terraform × ArgoCD, drift, contas AWS — está em
[`memory/celesta-infra.md`](memory/celesta-infra.md) e nos arquivos ao lado dele.

## Regras que valem aqui e não valem nos serviços

- **Terraform está significativamente desatualizado** em partes: mudanças foram aplicadas direto no
  console da AWS. Nunca assumir que o estado no código é o estado real — conferir antes de planejar
  qualquer mudança.
- **Produção é somente leitura.** Toda ação que muda estado é escrita para o Lucas executar, nunca
  executada aqui. Vale para `terraform apply`, `kubectl` que não seja `get`/`describe`, e qualquer
  coisa via console.
- **Perfil de AWS errado é o erro mais comum.** Confirmar com `aws sts get-caller-identity` antes de
  um comando que dependa de conta, não depois de ele falhar de um jeito confuso.
- Credenciais e identificadores de conta não entram neste repositório — ver `~/.claude-secrets/`.

## Onde as coisas moram

Os identificadores de conta, nomes de cluster, buckets de state e perfis estão nos arquivos de
memória deste diretório, que são versionados **sem** credencial. Se um valor for segredo, ele vai
para o vault e aqui fica só a referência.

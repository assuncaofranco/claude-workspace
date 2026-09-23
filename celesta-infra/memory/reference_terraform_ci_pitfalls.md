---
name: reference-terraform-ci-pitfalls
description: "Quatro defeitos de CI terraform que só aparecem rodando — precedência de credencial, git config --add, formas de source de módulo, nomes de ação IAM"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-17T06:29:24.339Z
---

Quatro defeitos encontrados no CEL-9173 (lrgi-terraform), todos em código que passou
por `fmt`, `validate` e revisão. Nenhum apareceu antes de rodar de verdade.

**1. Variável de ambiente ganha do `profile` na cadeia de credenciais do provider AWS.**

O sintoma é cruel: o **backend** do terraform respeita o `profile` e lê o state
certo, enquanto o **provider** segue o ambiente e confere os recursos em outra
conta. Não achando nada lá, o plan pede para criar tudo. No nosso caso:
`Plan: 129 to add`.

Acontece sempre que `aws-actions/configure-aws-credentials` exporta uma chave para
o ambiente e o profile no `~/.aws/credentials` diz `role_arn` +
`credential_source = Environment`.

Conserto: assumir a role **no próprio step** (`role-to-assume:`), e escrever o
profile com as credenciais temporárias resultantes. Aí as duas fontes são a mesma
identidade e a precedência deixa de importar. Precisa de
`role-skip-session-tagging: true`, senão exige `sts:TagSession` na trust policy.

E **rodar `aws sts get-caller-identity` antes de qualquer terraform**. Isso
transforma três runs de investigação em um.

**Importante para o celesta-terraform-infra:** ele escreve profiles exatamente
assim, e funciona por coincidência — a chave de ambiente é do user Administrator
da 502862189489, a mesma conta da role `celesta-infra-devops`. Mas os provider
aliases dele para prod-1, preprod e staging-1 podem estar lendo a conta errada em
silêncio. Não verificado. Ver [[project-cel8469-lrgi-terraform-audit]].

**2. `git config` sem `--add` substitui o valor da chave.**

Várias regras `url.<base>.insteadOf` escrevem a **mesma** chave. Sem `--add`, só a
última sobrevive e as outras desaparecem sem aviso. Provado localmente com
`HOME` temporário.

**3. Source de módulo vem em duas formas, e as duas precisam do token.**

Os roots usam `git@github.com:`, e os módulos referenciam uns aos outros com
`git::https://github.com/`. Reescrever só as formas SSH deixa os clones aninhados
saírem anônimos, e um repo privado então falha como se não existisse. O terraform
normaliza `git@host:path` para `ssh://git@host/path` antes de clonar, o que
explica por que a regra SSH cobre as duas formas SSH.

Cobrir as três:
```
for form in "git@github.com:" "ssh://git@github.com/" "https://github.com/"; do
  git config --global --add url."https://x-access-token:${TOKEN}@github.com/".insteadOf "$form"
done
```

**4. Nomes de ação IAM não seguem prefixo.**

`s3:GetBucketVersioning` e `s3:GetAccelerateConfiguration` são campos vizinhos do
mesmo recurso. Um plan num bucket lê umas vinte configurações, então lista
enumerada à mão quebra no próximo campo que alguém adicionar — quebrou no
primeiro run real, em `s3:GetAccelerateConfiguration` e
`dynamodb:DescribeTimeToLive`.

Escrever **largo por ação, estreito por recurso**: `s3:Get*`/`s3:Put*` restrito ao
ARN do bucket. Acesso a objeto não é afetado, porque essas ações exigem o recurso
`/*`.

# CLS-1283 Flipper — Deployment instructions

## Ordem

```
Deploy, em qualquer ordem:
celesta-wallet      CLS-3150
celesta-backoffice  CLS-3904
celesta-gateway     CLS-3905
celesta-cms-v2      CLS-3906
```

**Sem ordem.** Nenhum dos quatro chama o Flipper de outro serviço; cada um remove só o próprio client.
Nenhuma rota, payload, fila ou job muda. Prova: `git grep -i flipper` em `src` de cada branch volta
vazio, e no master nenhum `src/` chamava o client (só o wiring do DI e os testes).

**Sem migration.** Os quatro diffs são só remoção de arquivo e de linha de config.

**Sem biblioteca.** Nenhum `composer.json` ou `package.json` muda versão; o `package-lock.json` do
cms-v2 só perde as duas entradas do workspace `flipper`.

## Estados intermediários

Qualquer combinação de serviço novo com serviço velho é inofensiva: a flag não é lida por ninguém desde
CLS-2847/2848/2850/2851/2852, e o client removido não tinha chamador. Verificado localmente com os
quatro serviços novos, com e sem `FLIPPER_DATABASE_URL` no ambiente (coleção `flipper-smoke`, 7/7).

## O que não é código

- `FLIPPER_DATABASE_URL` continua nos manifests do argocd. Depois do deploy ninguém lê a variável, e
  Symfony e Strapi ignoram env não referenciada.
- Tirar a variável do argocd é passo separado do DevOps e só **depois** que nenhum rollback for
  previsto: o código velho ainda a referencia (no gateway, `%env(string:FLIPPER_DATABASE_URL)%` sem
  default).

## Rollback

Cada serviço volta sozinho, sem depender dos outros, enquanto a variável estiver no argocd.

## O que observar

Nada específico além do boot. No cms-v2, a imagem é construída do zero, então um `dist` velho com o
plugin não chega a produção.

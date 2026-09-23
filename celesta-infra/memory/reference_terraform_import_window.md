---
name: reference-terraform-import-window
description: "`terraform import` escreve no state compartilhado e abre uma janela de destroys até o código chegar na master"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-17T06:29:43.474Z
---

`terraform import` grava no **state compartilhado**, não numa cópia local. Se o
bloco de recurso está só na sua branch, qualquer pessoa que rode `plan` a partir
da master vê o recurso no state, não vê no código, e o plan pede **destroy**.

Aconteceu no CEL-8733/9173: 41 recursos (a role do CI mais 38 anexos de
`IAMUserChangePassword`) importados antes do merge. Um `apply` da master naquele
momento teria apagado o acesso do próprio pipeline. O TL quase rodou — foi pego
por aviso, não por trava.

Não apaga sozinho: o plan é barulhento e alguém vê. Mas parece que você quebrou
algo, e é exatamente a confusão que um épico de reconciliação existe para acabar.

**Regra prática:** importar e mergear devem ficar o mais perto possível no tempo.
Se não der, avisar o canal — quem mais aplica aquele root precisa saber antes de
rodar.

**Isso escala mal.** O CEL-8720 vai importar 20 repos ECR, 9 buckets, 2 users e a
stack do Jenkins. Importar tudo antes do merge deixaria a master pedindo dezenas
de destroys. Ali vale inverter a ordem: mergear o código primeiro com os blocos
declarados, aceitar que o plan mostre "to add" por alguns minutos — o apply
falharia com `EntityAlreadyExists`, então ninguém aplica por acidente — e só
então importar. Ou fatiar em PRs pequenos, um grupo de recursos por vez.

Método que funcionou para deixar o import com zero diff: escrever o código,
rodar `terraform plan`, **copiar o JSON renderizado do output do plan** em vez de
escrever o documento à mão, criar o objeto na AWS com esse JSON, importar, e
confirmar que o plan não mostra diff nenhum nele. `terraform console` não serve —
devolve `(known after apply)` para data source ainda não lido.

Duas armadilhas menores do mesmo dia:

- `terraform import` exige `-var-file` quando as variáveis não estão em
  `terraform.tfvars` nem em `*.auto.tfvars` no diretório do root. O erro não
  menciona o var-file.
- um loop `while read` sobre arquivo sem quebra de linha final engole a última
  entrada. Importou 37 de 38 e reportou zero falhas.

Ver [[reference-terraform-ci-pitfalls]] e
[[project-cel8469-lrgi-terraform-audit]].

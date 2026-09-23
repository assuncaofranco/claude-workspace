---
name: preprod-db-read
description: "Dá para ler o banco de qualquer serviço em preprod rodando dbal:run-sql dentro do pod, sem credencial de banco — verificado 2026-09-21 no preprod-1"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-21T15:01:40.728Z
---

Os preprods de casino são **namespaces de um único cluster EKS** (`celesta-preprod-cluster`, conta
852102753749, eu-west-1), então o mesmo `php bin/console dbal:run-sql` que o skill `db-query` usa
localmente roda dentro do container do serviço em preprod.

**Não é preciso credencial de banco.** A conexão é a da própria aplicação — nada de host/usuário/senha
de RDS para guardar em lugar nenhum, o que é justamente o que tornaria isso perigoso.

O passo a passo está no skill [[db-query]], seção "Preprod". Resumo do que erra fácil:

- precisa de sessão AWS viva (`awsmfa` no terminal do Lucas — código vivo, não dá para rodar sozinho);
- o container do PHP no pod é `<serviço>-phpfpm`; sem `-c` o kubectl pega o primeiro, que pode ser o nginx;
- namespace sempre explícito (`preprod-1`..`preprod-4`) — o namespace **é** o ambiente;
- kubeconfig separado no scratchpad, nunca o padrão do Lucas.

**Produção não.** Preprod sim, e só leitura.

**Por que vale a pena:** preprod é alterado à mão por muita gente, inclusive nas tabelas de permissão.
Boa parte do que parece bug de código é inconsistência de dado, e pela API isso é invisível — foi o
argumento do Lucas ao pedir esse acesso, e o primeiro uso já mostrou o valor: em 2026-09-21 a consulta
respondeu de uma vez que a migration do CLS-2980 não estava deployada e quais roles reais existiam
para testar cada perfil de permissão.

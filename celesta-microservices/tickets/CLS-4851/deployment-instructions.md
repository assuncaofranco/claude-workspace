# CLS-4851 — instruções de deploy

Escrito nos campos Deployment instructions e Rollback instructions do CLS-4851 e na descrição do
PR #1460 (2026-11-11).

## Deploy

1. Merge celesta-game #1460 (CLS-4852).

## Rollback

1. Revert celesta-game #1460 (CLS-4852).

## Por quê

- Uma entrega só, num serviço só. Nenhum contrato muda: rota, payload e resposta de
  `/game-gateways` ficam iguais, e a mudança fica dentro da `GameGatewayClientFactory`.
- Sem migration, config, variável de ambiente, fila ou biblioteca nova.
- Rollback: volta o comportamento antigo. Conexões com `""` gravado voltam a falhar na sincronização;
  a config 137 de produção, sem as chaves, segue funcionando.
- Depois do deploy, observar no Datadog o worker de sincronização: nenhum "URI must include a scheme
  and host" para `gateway_type_gamble_hub`.
- Release manifest: https://github.com/celesta-tech/celesta-releases/blob/main/releases/CLS-4851.yaml

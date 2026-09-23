---
name: reference-preprod-cluster-access
description: How to actually reach the casino preprod namespaces with kubectl — the celesta-preprod-2/3/4 contexts in the kubeconfig are broken
metadata: 
  node_type: memory
  type: reference
  originSessionId: e00fb548-2664-4d52-814a-94c1cf6a2485
  modified: 2026-09-14T07:56:22.756Z
---

The 4 casino preprods are **namespaces in a single EKS cluster**, `celesta-preprod-cluster` (account 852102753749, eu-west-1). Verified live 2026-09-14: `aws eks list-clusters --profile celesta-preprod --region eu-west-1` returns that one cluster and nothing else.

**The kubeconfig lies.** It has contexts `celesta-preprod-2`, `celesta-preprod-3`, `celesta-preprod-4` pointing at clusters `celesta-preprod-2-cluster` etc. Those clusters do not exist, and their exec blocks reference AWS profiles (`celesta-preprod-4`) that aren't in `~/.aws/config` either — only `celesta-preprod` is. Using them fails twice over ("config profile could not be found", then localhost:8080 refused).

**What works** (read-only, no change to Lucas's default kubeconfig):

```bash
export KUBECONFIG=<scratchpad>/kubeconfig-pp
aws eks update-kubeconfig --profile celesta-preprod --region eu-west-1 \
  --name celesta-preprod-cluster --kubeconfig "$KUBECONFIG"
kubectl -n preprod-4 get pods        # namespace = environment
```

Needs a live MFA session — see [[reference_aws_connection]]. Account/environment facts live in [[project_infra_context]].

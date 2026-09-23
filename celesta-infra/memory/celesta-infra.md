---
name: celesta-infra
description: Estrutura completa da infra Celesta — repos, ambientes, Terraform vs ArgoCD, estado atual e primeira tarefa
metadata:
  type: project
---

# Celesta Infra — Contexto Geral

Working directory: `/home/lucas/Desktop/infra`

## Repos presentes

| Repo | Função |
|------|--------|
| `celesta-casino-terraform` | Infra principal do casino (EKS, RDS, VPC, S3, IAM, ElastiCache, ACM, WAF, CloudFront, DocumentDB, etc.) |
| `celesta-sb-terraform` | Infra do sportsbetting — inclui prod-2 |
| `celesta-terraform-bi` | Infra de BI |
| `celesta-terraform-operator-bi` | Operador de BI |
| `celesta-argocd` | Manifests K8s do casino (kustomize base/overlays) |
| `celesta-argocd-parameters` | Valores por ambiente (prod-1, prod-2, preprod-1 a 4, staging-1, sb-preprod-1) |
| `celesta-sb-argocd` | Manifests K8s do sportsbetting |

## Terraform vs ArgoCD — distinção fundamental

- **Terraform**: gerencia a infra de nuvem (o "hardware virtual") — clusters EKS, bancos RDS, redes VPC, buckets S3, IAM, load balancers, etc.
- **ArgoCD**: gerencia o que roda *dentro* do Kubernetes — deployments das aplicações PHP/Go, ConfigMaps, Services, etc.
- São camadas independentes: Terraform cria o cluster, ArgoCD popula o cluster.

---

## celesta-casino-terraform

### Estrutura
```
celesta-casino-terraform/
  celesta-prod/
    prod-1/          ← produção casino (um .tf por recurso)
    quanta-aws/
    backend.tf       ← state S3: bucket=celesta-prod-terraform-new, região=eu-west-1
    terraform.tf     ← required_version = "1.9.5"
    variables.auto.tfvars
  celesta-preprod/   ← preprod-1, preprod-2, preprod-3, preprod-4 (subpastas)
  celesta-staging/
  modules/           ← módulos reutilizáveis (eks, rds, vpc, s3, iam_*, waf, etc.)
  kafka-acls/
  Makefile / terra.sh
  _specs/ _plans/ _rules/
```

### prod-1
- **Região:** eu-west-1
- **Conta AWS:** 413101478321
- **Perfil:** celesta-prod-1
- **Assume role:** arn:aws:iam::413101478321:role/celesta-prod-1-devops
- **State:** S3 bucket `celesta-prod-terraform-new`, DynamoDB lock `celesta-prod-terraform-new-lock`
- **Recursos declarados:** acm, aws-health-notifications, backup, backup_restore_testing, bastion, cloudfront, datadog, documentdb, dynamodb, efs, eks, elastic-cache, fluentbit, iam_groups, iam_policy, iam_roles, iam_users, ip_set, rds, route53, s3, sqs, ssm, vpc, waf

---

## celesta-sb-terraform

### Estrutura
```
celesta-sb-terraform/
  celesta-anj-prod-1/   ← É o prod-2 (nome confuso — ver nota abaixo)
  celesta-sb-preprod/
    preprod-1/          ← sub-ambiente com kafka-acls próprio
  celesta-sb-staging/   ← staging mínimo (só vpc + outputs)
  modules/              ← eks, rds, vpc, kafka, kafka-acls, elasticsearch, memorydb, cloudflare, etc.
  _specs/ _plans/ _rules/
```

### celesta-anj-prod-1 = prod-2 (mercado francês — sportsbetting)
> **Nota:** O diretório chama-se `celesta-anj-prod-1` (nome do perfil/conta AWS), mas internamente é o **prod-2**.
> prod-1 = casino irlandês (mercado completo: casino + sportsbetting + game).
> prod-2 = sportsbetting francês (ANJ — regulador francês). Não tem serviços de game/casino — é uma casa de apostas, não um casino completo. Estrutura de infra similar ao prod-1 mas sem os recursos de jogo.
- **Região:** eu-west-3 (Paris — diferente do casino prod-1 que é eu-west-1 / Irlanda)
- **Conta AWS:** 336536557570
- **Perfil:** celesta-anj-prod-1
- **Assume role:** arn:aws:iam::336536557570:role/celesta-anj-prod-1-devops
- **State:** S3 bucket `celesta-anj-prod-1-eu-west-3-terraform`, key `celesta-prod-2-terraform.tfstate`
- **kube_context:** celesta-prod-2
- **Recursos declarados:** alb, argocd, aws-health-notifications, backup, backup_restore_testing, bastion, cloudfront-s3, cloudfront, datadog, documentdb, dynamodb, eks, elastic-cache, elasticsearch, fluentbit, iam_policy, iam_roles, iam_users, ip_set, kafka, kafka-acls, rds, route53, s3, sqs, ssm, vpc, waf

### celesta-sb-preprod
- **Região:** eu-west-1
- **Conta AWS:** 688567272330
- **Perfil:** celesta-sb-preprod
- **Assume role:** arn:aws:iam::688567272330:role/celesta-sb-preprod-devops
- **State:** S3 bucket `celesta-sb-preprod-terraform`, DynamoDB `celesta-sb-preprod-terraform-lock`
- **Domínio:** octopo-sb-preprod.com
- **Recursos extras vs casino:** elasticsearch, kafka, cloudflare, cert_manager, ec2

### celesta-sb-staging
- **Perfil:** celesta-sb-staging
- **State:** S3 bucket `celesta-sb-staging-terraform`
- Workspace mínimo (só vpc + outputs declarados)

---

## celesta-argocd

### Estrutura
```
celesta-argocd/
  microservices/    ← um dir por serviço, cada um com kustomize/base + kustomize/overlays
  k8s-internals/    ← ferramentas do cluster (alb, cert-manager, fluentbit, autoscaler, rbac, etc.)
  apps/             ← ArgoCD Application definitions (um yaml por serviço)
  cel-apps/         ← variação de apps (possivelmente por cluster)
  _specs/ _plans/ _rules/
```

### Serviços declarados
activity, auth, backoffice, backofficefront, casino-gateway, celesta-website, cms, cmsv2, contact, crm, docs, document-validator, etl, fraud, game, gamego, gateway, mcp, notification-worker, payment, promotion, rundeck, scenario, scripts, segment, sensor, sportsbetting, statistics, toolgeoip, wallet

### Padrão kustomize
Cada microserviço tem `kustomize/base/` (definição base) + `kustomize/overlays/` (customizações por ambiente). Os valores específicos por ambiente ficam em `celesta-argocd-parameters`.

---

## celesta-sb-argocd

### Estrutura idêntica ao celesta-argocd
```
celesta-sb-argocd/
  microservices/    ← mesmos serviços do casino, adaptados ao sb
  k8s-internals/
  apps/
  _specs/ _plans/ _rules/
```

---

## celesta-argocd-parameters — ambientes presentes

| Ambiente | Terraform correspondente |
|----------|--------------------------|
| prod-1 | casino-terraform / celesta-prod/prod-1 |
| prod-2 | sb-terraform / celesta-anj-prod-1 |
| preprod-1 a 4 | casino-terraform / celesta-preprod/* |
| staging-1 | casino-terraform / celesta-staging |
| sb-preprod-1 | sb-terraform / celesta-sb-preprod |

---

## quanta-aws — conta legada em migração

**Conta AWS:** 954607206481 | **Perfil:** quanta-aws | **Região:** eu-west-1

### Histórico e contexto
Conta AWS original onde **todos** os microsserviços rodavam antes do Kubernetes (EC2/ECS clássico). É o prod real e atual — os jogadores estão aqui.

A migração para K8s começou gradualmente (prod-1, Ireland). Quando surgiu a oportunidade de criar a empresa de apostas na França (ANJ/prod-2), ela já nasceu em Kubernetes — mais simples pois ainda não está live.

O legado quanta-aws é mais complexo de migrar justamente por estar em produção ativa.

### Estado atual
- **quanta-aws:** prod real, live, todos os microsserviços rodando fora do K8s
- **prod-1 (Ireland):** K8s em construção, migração em andamento, ainda conectado ao quanta-aws
- **prod-2 (France):** K8s novo, sportsbetting apenas, **ainda não está live**

### O que está declarado no Terraform (quanta-aws/prod)
- `kafka-acls.tf` — ACLs do Kafka MSK (brokers: `celestaprod1.chnt4n.c9.kafka.eu-west-1.amazonaws.com`)
  - ACLs para as **marcas** (madnix, winoui, wildsultan, ibizapalace, yokikana, sakuraslots, spinwiz, slotscryptoonline) nos tópicos: balance-updated, document, promotion, balance, game, player-session, player, payment
  - ACLs para **bofront** nos tópicos: user, player, payment
- `aws-health-notifications.tf` — alertas de saúde AWS no Slack

### Evidências de migração incompleta
1. **NAT GW ainda no WAF de prod-1:** IP `54.77.39.190/32` está na whitelist do WAF de prod-1 com comentário `# NAT GW for quanta` — confirma que recursos em quanta-aws ainda se comunicam com o cluster EKS
2. **SSH key do bastion quanta em Rundeck:** `prod-1/rundeck/sealedsecrets/ssh-keys/ssh-key-bastion-quanta.yaml` — o Rundeck (em prod-1) ainda acessa o bastion da conta quanta via SSH
3. **Kafka ainda em quanta-aws:** o cluster MSK está na conta quanta, não em prod-1

### O que provavelmente existe na conta quanta mas não está no Terraform
Não é possível saber sem `terraform plan` ou acesso ao console, mas candidatos prováveis: EC2 (servidores de aplicação não migrados), RDS, outros recursos de rede. O Terraform de quanta-aws é mínimo demais para representar uma conta com microserviços rodando.

### "quanta" também aparece como game provider
Nos manifests do `gamego`, `/webhook/quanta/` é uma rota de webhook de um provider de jogos chamado Quanta — **contexto diferente**, não confundir com a conta AWS.

---

## Estado atual do Terraform

**Desatualizado.** Mudanças foram feitas diretamente no console AWS e nunca refletidas nos arquivos `.tf`. Existe drift entre o código e a realidade.

**Why it matters:** Drift torna futuras mudanças perigosas — o Terraform pode destruir ou recriar recursos que existem na AWS mas que ele "não conhece".

## Primeira tarefa

Reconciliar `celesta-casino-terraform/celesta-prod/prod-1` com o estado real da AWS.

**Passos:**
1. Configurar perfil AWS `celesta-prod-1` (`~/.aws/credentials` ou `~/.aws/config`)
2. `terraform init` — conecta ao state remoto no S3
3. `terraform plan` — compara código vs state vs AWS real
4. Analisar o output juntos para identificar drift

**Bloqueador atual:** credenciais AWS (Lucas ainda não tem os perfis configurados).

## Contexto do usuário

Lucas está começando em DevOps. Quer aprender os conceitos enquanto trabalha, não teoria prévia. Explicar o "porquê" de cada comando/decisão conforme avançamos.

**How to apply:** Sempre que rodar um comando ou propor uma mudança, explicar brevemente o que ele faz e por que — sem aulas teóricas longas antes de agir.

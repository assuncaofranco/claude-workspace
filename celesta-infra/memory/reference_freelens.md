---
name: reference-freelens
description: Lucas uses Freelens to visually inspect Kubernetes cluster structure — useful to point to during infra explanations
metadata: 
  node_type: memory
  type: reference
  originSessionId: d545471c-1778-4459-9ab7-cdae18a9bedf
  modified: 2026-09-02T14:32:22.118Z
---

Lucas has Freelens installed (a Lens-family Kubernetes GUI) and uses it to browse cluster structure: namespaces, nodes, pods, workloads. He flagged it himself as a good visualization aid for the [[project_infra_context]] DevOps study sessions.

**How to apply:** When explaining a Kubernetes concept that has a visual counterpart, point to where it shows up in Freelens — e.g. "abre o Freelens, clica em Nodes e você vê as máquinas reais que o Terraform criou" or "clica num Pod e olha em qual Node ele está rodando de verdade." Freelens talks to the same API server (`kube-apiserver`) described in [[feedback_teaching_style]]'s walkthrough — it's just another client asking it questions, the same way `kubectl` or ArgoCD do.

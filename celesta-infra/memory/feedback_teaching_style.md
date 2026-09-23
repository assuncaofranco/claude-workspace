---
name: feedback-teaching-style
description: "How to explain DevOps/infra concepts to Lucas — concrete/physical, needs-before-tools, short spaced paragraphs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d545471c-1778-4459-9ab7-cdae18a9bedf
  modified: 2026-09-02T14:32:21.098Z
---

Explain infra/DevOps concepts by grounding them in literal, physical machines and real installed processes — never describe something as "a set of processes" or another abstraction without immediately anchoring it to an actual machine, an actual running program, actual CPU/RAM. Lucas has strong low-level CS literacy (talks comfortably about processes, threads, pointers, CPU flow) but is new to DevOps-specific vocabulary — so keep the physical/computing grounding, but strip DevOps jargon unless it names a real, literal, installable thing (e.g. `kubelet`, `etcd`, `containerd` are fine — they're actual programs; abstract terms like "reconciliation loop" or "declarative state" are not, unless he asks).

**Why:** First attempt at explaining Kubernetes as "um conjunto de processos" was rejected as too abstract — Lucas said it didn't let him visualize it, make it real, imagine installing it. He explicitly asked to be walked through it "como se eu fosse um montador de servidores" (as if he were the one racking the servers).

**How to apply:**
- Use the needs → tool narrative structure ([[project_infra_context]] study goal) — state the concrete problem before naming the tool that solves it. This maps to the "genetic method" of teaching he asked about researching.
- When introducing any component, say what real thing it is (a background process on which machine, a text file in which repo, a database on disk) before naming it.
- Don't over-explain terms proactively — only unpack a concept when he asks; he said he'll ask when something's unclear, to keep the explanation from getting noisy.
- Write in short paragraphs (1-2 sentences) with blank lines between them — he loses his place in dense blocks of text.
- Avoid aphorisms, parables, or invented analogies (e.g. no "Kubernetes is like a shepherd") — literal walkthroughs of the real system only.
- Respond in Portuguese, matching his own register (informal, direct).
- See [[reference_freelens]] — a good tool to point to for making cluster structure visible during these explanations.

---
name: reference-jenkins-orphan-jobs
description: "Orphan/duplicate jobs in Jenkins — the two kinds (job-store leftover vs actively recreated by a stale casc_configs file), and how to tell them apart before acting"
metadata:
  node_type: memory
  type: reference
  originSessionId: e00fb548-2664-4d52-814a-94c1cf6a2485
  modified: 2026-09-14T11:49:19.616Z
---

**There is one Jenkins**, not one per environment: EC2 `celesta-infra-jenkins`, `i-091dc50364b26e2be`, account celesta-infra (502862189489), eu-west-1, private IP 10.1.16.120. It is **not** in Kubernetes — Freelens/kubectl will never find it. SSM agent is Online, so `aws ssm start-session --target i-091dc50364b26e2be --profile celesta-infra` gets you in with no SSH key or bastion; `aws ssm send-command` works for read-only checks. (`_specs/CEL-8230.md` claims separate prod and preprod Jenkins instances — not true as of 2026-09-14.)

`celesta-jenkins-config`'s README/CLAUDE.md say "removing a JCasC YAML does not remove the job from Jenkins" but not *why*. `jobs/jenkins/casc.jenkinsfile` does:

```sh
rm -rf $JENKINS_HOME/casc_configs/terraform
cp -r config/* $JENKINS_HOME/casc_configs/
```

`cp -r` with no prune — `terraform` is the only path ever deleted — and JCasC/job-dsl never deletes jobs it stops seeing.

**Two different kinds of orphan. Check which one before acting — the fix differs.**

| Kind | Symptom on disk | Fix |
|---|---|---|
| Job-store leftover | no YAML in `casc_configs/<vertical>/<env>/`, but dir exists under `/var/jenkins_home/jobs/celesta/jobs/<env>/jobs/<name>/` | delete the folder in the Jenkins UI — it does **not** come back |
| Actively recreated | stale YAML still sitting in `casc_configs/<vertical>/<env>/` | delete that file **first**, then the folder in the UI, else it returns within ~1 min |

Do not assume the second kind. Verified 2026-09-14: `cms-v2.yaml` was **not** in `casc_configs` (so `celesta/preprod-4/cms-v2` was a pure job-store leftover, frozen Jul 15 2025, one UI click to remove), while `proteus.yaml`, `swagger.yaml` and `toolgeoip-auto-updater.yaml` **were** still there despite being gone from git.

**Other practical notes**
- A rename leaves BOTH jobs visible, and only the new one gets the JCasC env vars (`APP`, `STAGE`, `CONTEXT`, `ECR_REPO`…). The orphan dies before its first stage — Stage View says "This Pipeline has not yet run". Real case: `celesta/preprod-4/cms-v2/deploy` (orphan) vs `celesta/preprod-4/cmsv2/deploy` (real), rename `c0c5510d` 2025-07-11, reported as CEL-9234.
- **Diagnosing a "broken" Jenkins job: compare the Full project name against what `config/` actually defines before debugging the pipeline.**
- List an env's orphan candidates from git: `git log --all --diff-filter=DR --name-status --format='' -- 'config/celesta/<env>/*.yaml' | grep -E '^[DR]' | awk '{print $2}' | sort -u`, keeping only paths that no longer exist — then confirm against the box, since git alone can't tell the two kinds apart.
- A durable fix would be `rsync --delete` instead of `cp -r`, but that wipes every orphan across all envs at once — raise with the team, don't do it quietly.

Repo context: [[project_infra_context]].

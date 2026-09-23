---
name: celesta-cms-v2-strapi-dev-gotchas
description: "Non-obvious local-dev and infra gotchas for celesta-cms-v2 (Strapi/Node) — bootstrap ordering bugs, npm workspace hoisting bug, domainId upload prefixing, kubectl OOM trap"
metadata: 
  node_type: memory
  type: project
  originSessionId: c737f90c-e477-433f-aa48-2a79b567a545
  modified: 2026-09-04T07:19:44.909Z
---

Interventions on this service are rare, so these are easy to re-forget between visits. Found while implementing CLS-1396 (S3 upload migration) in 2026-09.

## Local dev bootstrap (fresh checkout / fresh DB)

- **`license:load` ordering bug**: `entrypoint.sh` runs `node commands/apply-schema.js` then `npm run license:load` *before* `npm start`. `license:load` queries `strapi_core_store_settings`, which only gets created by Strapi's own migrations on first `strapi start` — so a brand-new empty database crash-loops forever, never reaching the step that would create the table. This is documented (independently, matches exactly) in `celesta-argocd`'s `microservices/cmsv2/RUNBOOK-provision-cmsv2-instance.md`, which calls the real fix "make `load-strapi-license.js` tolerate a missing table" — **not yet implemented in code** as of 2026-09-03.
  - **Workaround**: run `npm start` directly once (bypassing entrypoint.sh) against the fresh DB to let Strapi create its own tables, then bring the container up normally — the real entrypoint then succeeds.
- **`dist/` doesn't exist on a fresh checkout** (gitignored build artifact) and `docker-compose.dev.yml` bind-mounts `./api:/srv/app`, which shadows whatever `dist/` the Docker image built. Must run `npm run build:force` once (via `docker compose run`, so the anonymous `node_modules` volume matches the mounted source) before `npm start` will find anything to serve.
- **`npm ci` workspace-hoisting bug**: `npm ci` was failing to materialize `node_modules/react-intl` at root even though the lockfile correctly listed it — breaking `navigation-picker`'s TS build (`Cannot find module 'react-intl'`) both locally and in CI. Root cause looked like an npm-workspaces hoisting non-determinism (multiple react-intl versions nested under various `@strapi/*` packages competing with ours). **Fixed** by adding `"react-intl": "^7.1.11"` to the existing `overrides` block in `api/package.json` (which already pins `tar`/`axios`/`esbuild`/`ws` for similar reasons) — forces deterministic resolution. Verified with repeated clean `npm ci` runs before trusting it.
- **Regenerating `package-lock.json` from a directory that doesn't include `src/plugins/*`** silently drops all local workspace packages from the lock file (missing `bonus-list-picker`, `navigation-picker`, etc.) — always regenerate against the real, full `api/` directory (workspaces included), never a partial copy.

## Upload / S3 (CLS-1396)

- Files get prefixed with a numeric **domainId** (e.g. `5-image.png`) via `src/utils/upload/prefixUploadsWithDomainId.ts`, wired globally in `src/index.ts`. It resolves the id by calling **CRM** (`GET {CRM_HOST}/en/api/domains?slug=<slug>`), where `slug` comes from `DOMAIN_SLUG` env var (local dev) or is parsed from the request's Host header (prod/preprod, since `DOMAIN_SLUG` isn't set there). Guard-signed via `GUARD_KEY`.
  - This is **unrelated** to `src/middlewares/extractDomainId.ts` (a koa middleware reading `:domainId` from a route param) — that middleware exists, is unit-tested, but isn't wired to any route anywhere in the codebase. Don't confuse the two.
  - Brand-level bucket separation (madnix vs wildsultan sharing one bucket) is handled separately, via `CMS_ASSET_PATH` → S3 `rootPath` (e.g. `cms-v2/madnix`), already set per-brand in `celesta-argocd-parameters`.
  - Matches the same pattern celesta-backoffice uses for its own multi-tenant S3 paths (domain/game/bonus assets prefixed with a real `domainId` from a route param) — not a novel pattern for this ticket.
- Strapi's own `@strapi/upload` core (`image-manipulation.generateFileName`) already appends a random hex suffix to every upload — collisions were never really possible even before the domainId prefix; the prefix is about bucket organization, not the primary safety net.

## Infra facts (preprod-1)

- cmsv2 pods live in **per-environment namespaces** (`preprod-1`, `preprod-2`, ... `prod-1`), **not** a shared `celesta` namespace.
- Real preprod-1 hostnames (found via the Ingress, not guessable from the staging runbook's `cmsv2-<brand>.staging-1...` pattern): madnix → `casino.preprod-1.octopodev.com`, wildsultan → `celesta.preprod-1.octopodev.com`.
- **`kubectl exec` shares the target container's memory cgroup** — running `node commands/admin.js create-user` inside the already-running server pod OOM-killed it (preprod-1's limit is only 462Mi). Kubernetes auto-restarted it within seconds, so low lasting impact, but avoidable. **Safer pattern**: spin up a standalone one-off Pod with the same image + `envFrom` (configMapRef + secretRef matching the real deployment) to run any one-shot admin/management command, then delete the pod — doesn't compete with the live server's memory limit. See [[celesta-cms-v2-preprod-1-test-admin]] for where this was used.
- See [[reference-infra-repos]] for the repo map (`celesta-argocd`, `celesta-argocd-parameters`) this was all discovered in.
- **Preprod scales down overnight** (per Lucas, 2026-09-04) — pods get destroyed and recreated fresh. Anything uploaded to the `local` provider the day before will be gone the next morning *regardless* of whether the S3 fix works. Don't mistake this nightly cycle for the bug resurfacing — and it doubles as a free "survives a redeploy" check each morning without needing to manually trigger one.

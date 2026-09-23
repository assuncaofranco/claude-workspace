---
name: project_cls2387_cms_two_branches
description: CLS-2387 in celesta-cms lives on TWO similarly-named branches; which one is the base and which is the follow-up
metadata: 
  node_type: memory
  type: project
  originSessionId: b16f9ff8-c751-4552-a0c3-e7894f293121
  modified: 2026-09-04T15:46:43.514Z
---

`CLS-2387` in **celesta-cms** (not cms-v2) exists as two branches, easy to confuse:

- **`CLS-2387`** — the base ticket: a **bulk render endpoint** for custom email templates (`renderBulk()` + `MemberzoneClient::getCustomersByDomain()` + a locale-batching refactor of `resolveContent`).
- **`CLS-2387-custom-attrbiutes`** (note the typo *attrbiutes*, it's in the real branch name) — the **follow-up**, built on top of the base: applies player custom attributes to the bulk render, plus "remove player-count limit from memberzone customers request". It is *ahead* of the base branch.

When asked to "merge master into CLS-2387", check which one actually conflicts — the follow-up branch tends to already carry a master merge on the remote while the base one is behind.

**The conflict source (resolved 2026-09-04 on the base branch, merge `2a1c278`):** master had landed `CLS-1904-CLS-2482` — *player custom attributes in the single `/render`* — which touches exactly the same three files as the bulk endpoint (`MemberzoneClient`, `CustomEmailTemplateRenderer`, `tests/Traits/MemberzoneMockTrait`). Every conflict was a "both sides added code in the same slot" union, **except** one non-textual consequence: master added a `LoggerInterface` constructor arg to the renderer, so the base branch's four 2-arg `new CustomEmailTemplateRenderer(...)` calls in `CustomEmailTemplateRendererTest` break silently — git auto-merges the file with no marker. Always grep `new <Service>(` after merging a branch that changed a constructor.

Deliberately *not* done in that merge: `renderBulk()` still does not resolve custom attributes (`{{ player.custom_attributes.* }}` renders empty in bulk). That integration is the follow-up branch's whole job — see `6d112c8`.

See [[custom-attributes-bundle-mechanics]] for how the bundle stores/resolves attributes.

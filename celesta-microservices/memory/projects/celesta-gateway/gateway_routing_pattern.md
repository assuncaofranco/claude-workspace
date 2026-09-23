---
name: Gateway routing pattern for player endpoints
description: Player-facing gateway URLs never include domainId/playerId in path — they come from the OAuth2 token
type: project
originSessionId: c2906b35-7daf-4bab-af2c-ca3eb9157cad
---
Player-facing endpoints in celesta-gateway do NOT include `{domainId}` or `{playerId}` in the URL path. These are extracted from the authenticated OAuth2 user token inside the controller:

```php
$user = $this->getUser();
$domainId = $user->getDomainId();
$playerId = $user->getId();
```

Internal calls to backend microservices (promotion, wallet, etc.) DO use the full path format:
`api/domain/{domainId}/player/{playerId}/...`

All inter-service calls use `'guard_protected' => true` in the CurlClient options.

**Why:** The gateway acts as an OAuth2 server; the player identity comes from the JWT token, not the URL. Putting domainId/playerId in the public URL would be redundant and insecure.

**How to apply:** When adding a new player-facing endpoint to the gateway, never add `{domainId}` or `{playerId}` to the route path. Always call PromotionClient (or other clients) with the values from `$this->getUser()`.

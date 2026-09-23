---
name: Email system architecture and diagnostics
description: Full map of the transactional email flow across celesta-backoffice, celesta-crm and celesta-contact — tables, providers, debug queries, Postman testing
type: reference
originSessionId: a3f8d741-6899-4931-a7b7-49dc7f5d0e31
---
## Flow

```
Player action (gateway → CRM)          BO user action (backoffice)
        │                                        │
dispatches TransactionalEmailJob                 │
via Symfony Messenger                            │
        │                                        │
        └──────────── celesta-backoffice ─────────┘
                      picks up the job
                      looks up template in DB
                      calls ContactClient::postEmail()
                              │
                        celesta-contact
                        POST /emails
                        dispatches EmailMessageJob (async)
                              │
                        SendGrid or EDP provider
                        records result in email_history
```

**CRM triggers**: account_created, email_verification, player_forgot_password, account_closed, account_enabled, account_excluded — all via `TransactionalEmailJob` dispatched to Messenger, NOT direct HTTP to celesta-contact.

**Backoffice job handlers**:
- `WebsiteTransactionalEmailJobHandler` — player/website emails
- `UserTransactionalEmailJobHandler` — BO user emails

---

## Database tables by service

### celesta-backoffice

| Table | Purpose |
|---|---|
| `website_transactional_email` | Player email templates (subject + content), per domain_id |
| `user_transactional_email` | BO user email templates (no domain_id) |
| `website_asset_translations` | Per-locale translations for player templates (Gedmo Translatable) |
| `ext_translations` | Per-locale translations for BO user templates (Gedmo default) |

`website_transactional_email` and `user_transactional_email` both inherit from `transactional_email` via FK (joined table inheritance). The `event` column is in the parent table.

**Known event types** (website/player):
`account_created`, `player_forgot_password`, `forget_password`, `change_password_confirmation`, `deposit_success`, `deposit_failed`, `withdrawal_requested`, `withdrawal_paid`, `withdrawal_refused`, `withdraw_canceled`, `email_verification`, `email_verification_confirmation`, `bonus_offered_manually`, `account_closed`, `account_excluded`

**Valid template variables** (website):
`website.name`, `player.first_name`, `player.last_name`, `player.email`, `player.username`, `player.password`, `player.email_verification`, `player.exclusion_end_at`, `player.cool_off_end_at`, `deposit.amount`, `deposit.movement_id`, `deposit.movement_date`, `withdrawal.amount`, `withdrawal.movement_id`, `withdrawal.movement_date`, `real_balance`, `temporary_password_token`, `current_year`, `website.url`, `website.support_email`, `website.support_phone_number`, `website.login_url`

**Valid template variables** (user/BO):
`user.first_name`, `user.last_name`, `first_login.link`, `forgot_password.link`, `current_year`

### celesta-contact

| Table | Purpose |
|---|---|
| `provider` | Base provider row: `id`, `enabled`, `domain_id`, `retry_send_count`, `discr` (edp/sendgrid) |
| `sendgrid_provider` | Extends provider: `api_key_id`, `api_key` |
| `edp_provider` | Extends provider: `client_id`, `client_secret`, `base_url` |
| `email_history` | Audit log of every send attempt |

`email_history` columns: `id`, `status` (pending/failure/success), `from_email`, `to_email`, `subject`, `message_length`, `response_status`, `response_body` (contains `email_uid` on EDP success), `created_at`, `updated_at`

---

## Diagnostic queries

### 1. Check player templates exist for a domain
```sql
-- celesta-backoffice DB
SELECT id, subject, content
FROM website_transactional_email
WHERE domain_id = <domain_id>;
```

### 2. Check BO user templates
```sql
-- celesta-backoffice DB
SELECT id, subject, content
FROM user_transactional_email;
```

### 3. Check translations for a player template
```sql
-- celesta-backoffice DB
SELECT field, content, locale
FROM website_asset_translations
WHERE object_class LIKE '%WebsiteTransactionalEmail%'
  AND foreign_key = <template_id>
ORDER BY locale;
```

### 4. Check provider is enabled and has credentials
```sql
-- celesta-contact DB
SELECT p.id, p.enabled, p.domain_id, p.discr, p.retry_send_count,
       s.api_key,
       e.client_id, e.client_secret, e.base_url
FROM provider p
LEFT JOIN sendgrid_provider s ON s.id = p.id
LEFT JOIN edp_provider e ON e.id = p.id
WHERE p.domain_id = <domain_id>;
```

### 5. Check email history for a recipient
```sql
-- celesta-contact DB
SELECT id, status, from_email, to_email, subject,
       message_length, response_status, response_body, created_at
FROM email_history
WHERE to_email = '<email>'
ORDER BY created_at DESC
LIMIT 20;
```

---

## Failure point checklist

| Symptom | Check | Table |
|---|---|---|
| No row in email_history | Template missing for event+domain, or Messenger queue stuck | `website_transactional_email` |
| history row, status=failure | `response_body` has provider error | `email_history` |
| history row, status=success, email not received | Wrong `to_email` in CRM, spam filter, bad sender domain (SPF/DKIM), plain-text template | `email_history` + CRM `customer` |
| history row, status=success, message_length tiny | Template variables not resolving (wrong variable name) | `website_transactional_email` |
| No enabled provider for domain | Provider row missing or `enabled=0` | `provider` table |

---

## Testing directly via Postman

### EDP provider — two steps
Get `base_url`, `client_id`, `client_secret` from `edp_provider` table.

**Step 1 — auth**
```
POST <base_url>/api/auth
Content-Type: application/x-www-form-urlencoded

client_id=<client_id>&client_secret=<client_secret>
```
Response: `{ "token": "..." }`

**Step 2 — send**
```
POST <base_url>/api/send
Content-Type: application/x-www-form-urlencoded
Authorization: <token>

to_email=player@example.com
from_name=Test
from_email=owner@quanta.lu
subject=Test
body=<p>Hello</p>
plain_text=Hello
send_at=2026-05-12 10:00:00+00:00
```

### SendGrid — one step
Get `api_key` from `sendgrid_provider` table.
```
POST https://api.sendgrid.com/v3/mail/send
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "personalizations": [{ "to": [{ "email": "player@example.com" }] }],
  "from": { "email": "owner@quanta.lu", "name": "Test" },
  "subject": "Test",
  "content": [{ "type": "text/html", "value": "<p>Hello</p>" }]
}
```

---

## Testing celesta-contact POST /emails directly

All routes use `guard_protected: true` — requires `X-Guard-Secret` header.

Signature: `HMAC-SHA256(key=GUARD_KEY, data=METHOD+HOST+PATH+md5(body))`

Postman pre-request script:
```javascript
const body = pm.request.body.raw;
const guardKey = pm.environment.get("GUARD_KEY");
const host = pm.request.url.getHost();
const path = "/" + pm.request.url.path.join("/");
const bodyMd5 = CryptoJS.MD5(body).toString();
const data = "POST" + host + path + bodyMd5;
const secret = CryptoJS.HmacSHA256(data, guardKey).toString();
pm.request.headers.add({ key: "X-Guard-Secret", value: secret });
```

Request body:
```json
{
  "receivers": [{ "email": "player@example.com", "name": "Player" }],
  "sender_email": "owner@quanta.lu",
  "sender_name": "Madnix",
  "subject": "Test",
  "body_html": "<p>Hello</p>",
  "body_text": "Hello",
  "domain_id": 56
}
```

If `GUARD_ENABLED=false` in dev `.env`, skip the header entirely.

---

## Key source files

| File | Purpose |
|---|---|
| `celesta-backoffice/src/Library/ContactClient.php` | HTTP client to celesta-contact |
| `celesta-backoffice/src/AppBundle/Handler/WebsiteTransactionalEmailJobHandler.php` | Processes player email jobs |
| `celesta-backoffice/src/AppBundle/Handler/UserTransactionalEmailJobHandler.php` | Processes BO user email jobs |
| `celesta-backoffice/src/GatewayBundle/Entity/WebsiteTransactionalEmail.php` | Player template entity + all event/variable constants |
| `celesta-backoffice/src/GatewayBundle/Entity/UserTransactionalEmail.php` | BO user template entity |
| `celesta-contact/src/ContactBundle/Controller/ContactController.php` | POST /emails endpoint |
| `celesta-contact/src/AppBundle/Provider/EDPClientProvider.php` | EDP send logic |
| `celesta-contact/src/AppBundle/Provider/SendGridClientProvider.php` | SendGrid send logic |
| `celesta-crm/src/ApiBundle/Controller/CustomerPasswordController.php` | Player forgot password trigger |
| `celesta-crm/src/CustomerBundle/EventListener/StatusStackSubscriber.php` | Account status email triggers |

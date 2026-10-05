# Credential handling conventions

How agents get access to client sites without ever holding a persistent copy of the
credential themselves. Read alongside `CONVENTIONS.md` — secret access events use the
same changelog, just a different entry shape.

## Principle order (highest priority first)

1. **Avoid storing a raw credential at all if there's a scoped-access alternative.**
   OAuth tokens (Google Search Console, GA4) and scoped API keys (WordPress
   Application Passwords) are revocable independently and never expose the client's
   actual account password. The portal should default to these paths and only fall
   back to a raw password field for platforms with no alternative.
2. **When a raw credential is unavoidable, it lives in a dedicated secrets manager**
   (HashiCorp Vault, AWS Secrets Manager, or Google Secret Manager) — never encrypted
   fields in the portal's own application database. The portal database holds a
   secret reference ID and nothing else.
3. **Agents fetch just-in-time and never persist.** A credential is retrieved for one
   task, used, and discarded from memory when the task ends. No SKILL.md, no task
   record, no changelog entry, and no dashboard ever contains a secret's actual value.
4. **Every access is logged, every credential is revocable, nothing is silent.**

## What lives where

```
Portal database:        client_id → secret_ref_id (opaque reference only)
Secrets manager:         secret_ref_id → actual credential (encrypted at rest,
                          envelope encryption: per-client data key wrapped by a
                          master key, so no single key decrypts everything)
~/.hermes/state/:        NEVER holds credential values — only access log entries
```

## Secret access log entry

Append-only, same file family as the client changelog
(`~/.hermes/state/changelog/<client>.jsonl`), but a distinct entry type so
`progress-dashboard` and any future audit tooling can filter it separately:

```json
{
  "type": "secret_access",
  "timestamp": "2026-08-03T14:40:00+03:00",
  "client": "example.com",
  "agent": "technical-health",
  "task_id": "th-0042",
  "secret_ref_id": "sec_9f2a...",
  "secret_kind": "wordpress_application_password",
  "action": "retrieved for redirect verification, used, discarded",
  "outcome": "success"
}
```

`secret_kind` is one of a known set (`google_oauth_token`, `wordpress_application_password`,
`ga4_service_account`, `raw_password` — flag `raw_password` entries for extra scrutiny,
since they're the fallback case, not the default). The log NEVER contains the secret
value, only that an access happened, what kind, and whether it succeeded.

## Rotation and offboarding

- [ ] Every credential kind has a default expiry/rotation reminder (OAuth tokens
  typically self-expire; raw passwords and API keys need an explicit reminder cadence
  — 90 days is a reasonable default absent a client-specific reason otherwise).
- [ ] Engagement closure (still an open item in the overall pipeline — see prior
  priority list) MUST include revoking every credential tied to that client in the
  secrets manager, not just marking the engagement as closed in the portal.
- [ ] A credential that fails on retrieval (revoked, expired, wrong scope) is a
  `blocked` task with `blocked_reason` naming the credential kind — never a silent
  failure or a guess at a workaround.

## What this does not cover

Payment card data is handled entirely by the payment processor (Stripe/Paddle) via
their hosted checkout or tokenized elements — it never enters this system at all, and
this document intentionally says nothing about card data because the operator should
never be in a position where it needs to.

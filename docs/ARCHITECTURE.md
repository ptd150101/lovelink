# Architecture

LoveLink uses a monorepo with a Next.js frontend, Django ASGI backend, PostgreSQL, Redis, Celery, S3-compatible object storage and a self-hosted LiveKit OSS node.

## Trust boundaries

1. Browser receives only public profile data, session cookies, signed upload URLs and short-lived LiveKit participant tokens.
2. Django owns authorization, state machines, moderation and auditability.
3. LiveKit owns media transport only; it does not decide who may call whom.
4. Verification evidence is private and staff access is role-gated and audited.
5. Redis is ephemeral coordination infrastructure; PostgreSQL is the source of truth.

## State machines

- Account: pending_verification -> active -> suspended/banned -> scheduled_for_deletion -> deleted
- Profile: draft -> published -> hidden_by_user/hidden_by_moderator/suspended
- Connection: pending -> accepted/declined/cancelled/expired/blocked
- Call: created -> ringing -> accepted -> connecting -> active -> ended; terminal alternatives declined/cancelled/missed/failed
- Verification: draft -> submitted -> in_review -> needs_more_info/verified/rejected/expired/revoked
- Report: open -> in_review -> action_taken/dismissed/escalated

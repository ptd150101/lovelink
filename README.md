# LoveLink

LoveLink is a full-stack dating-platform MVP focused on verified profiles, structured discovery, consensual connections, private messaging and self-hosted 1-to-1 video calls.

## Frozen MVP scope

The repository implements the complete frozen MVP checklist agreed for this project:

- Registration, email verification/resend, session login/logout, password recovery/change and temporary login lockout after repeated failures
- Private phone-number verification through six-digit OTP, with hashed codes, expiry, resend cooldown, attempt limits, daily limits and pluggable console/Twilio SMS delivery
- Four-step profile onboarding, editable profile, per-field privacy controls, hide/publish states and delayed account deletion
- Profile-photo upload through S3-compatible presigned URLs, interactive 4:5 cropping, server-side 4:5 normalization, EXIF removal, drag-and-drop ordering and primary-photo selection
- Discovery with gender, age, height, current province, hometown, occupation, education, income, relationship goal, identity verification, has-photo and recently-active filters; all categorical filters support multiple choices
- Privacy-aware profile detail, identity-verification and phone-verification badges, and connection-only coarse online/recently-active presence
- Intro requests with accept, decline, cancel, expiry, disconnect and spam limits
- Private 1-to-1 realtime messaging after mutual connection, durable read receipts, unread counts, reconnect and REST catch-up for messages missed while the WebSocket was unavailable
- Self-hosted LiveKit OSS 1-to-1 video calls with ringing, incoming-call recovery after reload/reconnect, accept, decline, cancel, missed call, end, webhook reconciliation, connection-quality display, camera switching and audio-only fallback
- Manual identity verification with private evidence, challenge selfie, reviewer queue, signed evidence access, approve/reject/request-more-information, revocable badge and access/decision audit logs
- Customized Django Admin workspaces for reviewers and moderators with structured actions and enforceable encrypted TOTP MFA for staff accounts
- In-app notifications plus preference-aware email notifications for connections, messages, verification outcomes and security warnings; message bursts are coalesced per conversation
- Blocking, reporting, warnings, image/profile hiding, temporary suspension, permanent bans, badge revocation and moderation audit history
- Account preferences, online-status privacy, blocked-user management, email changes, session revocation and deletion grace period
- Optional Sentry integration, structured JSON logs and application health endpoint
- Docker Compose, MinIO, PostgreSQL, Redis, Celery and LiveKit OSS
- Backend unit/integration tests, frontend browser tests and a Docker-backed full-stack Playwright workflow using real Django, PostgreSQL, Redis, MinIO, session auth and WebSocket messaging

Features explicitly outside this frozen MVP include social feed, public comments, stories, livestream, group chat/calls, virtual currency, boosts/payments, AI matching, recordings, file/voice-message chat, social login and native mobile applications.

## Architecture

```text
Next.js web  -> Django REST / Channels -> PostgreSQL
                         |              -> Redis / Celery
                         |              -> S3-compatible storage
                         |              -> SMTP / SMS provider
                         `--------------> LiveKit OSS
```

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Web: http://localhost:3000
- API health: http://localhost:8000/healthz
- Django admin: http://localhost:8000/admin
- MinIO console: http://localhost:9001

The backend is an uv project requiring Python `>=3.13,<3.14`. Dependencies are declared in `backend/pyproject.toml` and pinned by `backend/uv.lock`. No host Python or uv installation is required for Docker Compose. For native backend development, install uv and follow [`docs/local-development.md`](docs/local-development.md); the first `uv run` automatically obtains Python when needed, creates `.venv` and synchronizes dependencies.

For local phone verification, `SMS_BACKEND=console` writes the OTP to backend logs. A deterministic `PHONE_OTP_FIXED_CODE` may be used only in local development or E2E testing and must remain empty in production.

Create an admin account and enroll its authenticator:

```bash
docker compose exec backend uv run python manage.py createsuperuser
docker compose exec backend uv run python manage.py enroll_staff_mfa admin@example.com
```

After all staff accounts are enrolled, production may enforce MFA globally with `STAFF_MFA_REQUIRED=true`.

Apply committed database migrations:

```bash
docker compose exec backend uv run python manage.py migrate
```

Run the standard test suites:

```bash
docker compose exec backend uv run pytest
cd frontend && npm ci && npm run lint && npm run build && npm run test:e2e
```

Run backend tests natively through the uv-managed project environment:

```bash
cd backend
uv run pytest
```

Run the deterministic full-stack browser flow locally:

```bash
# Add PHONE_OTP_FIXED_CODE=123456 to the local .env used only for this test.
docker compose exec backend uv run python manage.py seed_e2e
cd frontend
FULLSTACK_E2E=1 PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e -- --project=chromium e2e/fullstack.spec.ts
```

## Security notes

- Verification evidence is stored in a private bucket and exposed only through short-lived signed URLs; every reviewer access is audited.
- A reviewer cannot approve a request until all required evidence types are present.
- Phone OTP values are never stored in plaintext and verified phone numbers are never exposed publicly.
- Staff TOTP secrets are encrypted at rest and accepted time steps cannot be replayed.
- LiveKit API secrets stay server-side; browser tokens are room-specific and short-lived.
- Profiles are visible only to authenticated active members.
- Chat and calls require an accepted connection and are denied when either side blocks the other.
- Presence is coarse, connection-only and disabled when the target user turns off online-status sharing.
- Production must use HTTPS, real SMTP/SMS providers, strong secrets, JSON log shipping, Sentry or equivalent monitoring, object-storage lifecycle rules, encrypted backups, enforced staff MFA and a reviewed legal/privacy policy.

See `docs/` for the detailed architecture, API and operations guides.

# LoveLink

LoveLink is a full-stack dating-platform MVP focused on verified profiles, structured discovery, consensual connections, private messaging, and self-hosted 1-to-1 video calls.

## Included MVP scope

- Registration, email verification/resend, session login/logout, password recovery and password change
- Four-step profile onboarding, editable profile, privacy controls and profile visibility
- Profile-photo upload through S3-compatible presigned URLs, drag-and-drop ordering and primary-photo selection
- Discovery with age, height, current province, hometown, occupation, education, income, relationship-goal and verified-only filters
- Profile detail with privacy-aware fields and connection-only online/recently-active presence
- Intro/connection requests with accept, decline, cancel and disconnect states
- Private 1-to-1 realtime messaging after mutual connection
- Self-hosted LiveKit OSS 1-to-1 video calls with ringing, incoming-call recovery after reload/reconnect, accept, decline, cancel, missed call, end and webhook reconciliation
- Manual identity-verification workflow with private evidence, reviewer queue, approve/reject/request-more-information and revocable verified badge
- Customized Django Admin workspaces for reviewers and moderators, including signed evidence access and structured decision forms
- In-app notifications plus preference-aware email notifications for connections, messages, verification outcomes and security warnings
- Blocking, reporting, suspension, moderation actions and audit logs
- Account privacy settings, hide profile, blocked-user management and delayed account deletion
- Docker Compose, MinIO, PostgreSQL, Redis, Celery and LiveKit OSS
- Backend unit/integration tests, mocked frontend browser tests and a Docker-backed full-stack Playwright workflow

## Architecture

```text
Next.js web  -> Django REST / Channels -> PostgreSQL
                         |              -> Redis / Celery
                         |              -> S3-compatible storage
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

Create an admin account:

```bash
docker compose exec backend python manage.py createsuperuser
```

Apply committed database migrations:

```bash
docker compose exec backend python manage.py migrate
```

Run the standard test suites:

```bash
docker compose exec backend pytest
cd frontend && npm ci && npm run lint && npm run build && npm run test:e2e
```

Run the deterministic full-stack browser flow locally:

```bash
docker compose exec backend python manage.py seed_e2e
cd frontend
FULLSTACK_E2E=1 PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e -- --project=chromium e2e/fullstack.spec.ts
```

## Security notes

- Verification evidence is stored in a private bucket and exposed only through short-lived signed URLs; every reviewer access is audited.
- A reviewer cannot approve a request until all required evidence types are present.
- LiveKit API secrets stay server-side; browser tokens are room-specific and short-lived.
- Profiles are visible only to authenticated active members.
- Chat and calls require an accepted connection and are denied when either side blocks the other.
- Presence is coarse, connection-only and disabled when the target user turns off online-status sharing.
- Production must use HTTPS, trusted email delivery, strong secrets, object-storage lifecycle rules, encrypted backups, MFA for staff and a reviewed legal/privacy policy.

See `docs/` for the detailed architecture, API and operations guides.

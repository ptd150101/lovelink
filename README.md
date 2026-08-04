# LoveLink

LoveLink is a full-stack dating-platform MVP focused on verified profiles, structured discovery, consensual connections, private messaging, and self-hosted 1-to-1 video calls.

## Included MVP scope

- Registration, email verification, session login/logout, password recovery and password change
- Four-step profile onboarding, editable profile, privacy controls and profile visibility
- Profile-photo upload through S3-compatible presigned URLs
- Discovery with age, height, current province, hometown, occupation, education, income, relationship-goal and verified-only filters
- Profile detail with privacy-aware fields
- Intro/connection requests with accept, decline and cancel states
- Private 1-to-1 realtime messaging after mutual connection
- Self-hosted LiveKit OSS 1-to-1 video calls with ringing, accept, decline, cancel, missed call, end and webhook reconciliation
- Manual identity-verification workflow with private evidence, reviewer queue, approve/reject/request-more-information and revocable verified badge
- In-app notifications and account/security email notifications
- Blocking, reporting, suspension, moderation actions and audit logs
- Account privacy settings, hide profile, blocked-user management and delayed account deletion
- Django admin and reviewer/moderator APIs
- Docker Compose, MinIO, PostgreSQL, Redis, Celery and LiveKit OSS
- Backend unit/integration tests and Playwright browser smoke tests

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

Run the test suites:

```bash
docker compose exec backend pytest
cd frontend && npm ci && npm run lint && npm run build && npm run test:e2e
```

## Security notes

- Verification evidence is stored in a private bucket and exposed only through short-lived signed URLs.
- LiveKit API secrets stay server-side; browser tokens are room-specific and short-lived.
- Profiles are visible only to authenticated active members.
- Chat and calls require an accepted connection and are denied when either side blocks the other.
- Production must use HTTPS, trusted email delivery, strong secrets, object-storage lifecycle rules, encrypted backups, MFA for staff and a reviewed legal/privacy policy.

See `docs/` for the detailed architecture, API and operations guides.

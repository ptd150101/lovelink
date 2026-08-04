# Operations

## Production checklist

- Replace all development secrets and pin container-image versions.
- Use HTTPS for app/API/LiveKit and configure trusted origins.
- Configure production SMTP and SMS providers.
- Run PostgreSQL and Redis with authentication, backups and restricted networks.
- Enroll every staff account in TOTP MFA, then set `STAFF_MFA_REQUIRED=true`.
- Set `LOG_FORMAT=json`, configure `SENTRY_DSN` and connect uptime checks to `/healthz`.
- Put LiveKit on a VM with public IPv4, trusted TLS and the required ICE/TURN ports.
- Configure object-storage lifecycle policies for verification evidence.
- Test database and object-storage restore before public beta.
- Review privacy, consent, data retention, age gating, phone-number handling and identity-document handling with legal counsel.

## Phone OTP and SMS

Local development defaults to:

```env
SMS_BACKEND=console
PHONE_DEFAULT_COUNTRY_CODE=84
PHONE_OTP_TTL_SECONDS=300
PHONE_OTP_RESEND_SECONDS=60
PHONE_OTP_DAILY_LIMIT=5
PHONE_OTP_MAX_ATTEMPTS=5
```

The console backend writes the OTP to Django logs. For deterministic E2E only, `PHONE_OTP_FIXED_CODE=123456` may be set while `DJANGO_DEBUG=true`.

Production Twilio configuration:

```env
SMS_BACKEND=twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
# Or use TWILIO_MESSAGING_SERVICE_SID instead of TWILIO_FROM_NUMBER.
PHONE_OTP_FIXED_CODE=
```

Operational requirements:

1. Keep the fixed-code variable empty in production; settings ignore it when debug mode is off.
2. Restrict SMS credentials to the production secret store.
3. Configure provider spend/fraud alerts and geographic permissions.
4. Monitor 429 rates, failed sends and unusual destination patterns.
5. Phone numbers remain private application data; only the verified/not-verified badge is public.
6. OTPs are hashed in the database, expire, have attempt limits, resend cooldowns and per-user daily limits.

## Authentication abuse protection

Login attempts are protected by API throttling plus temporary cache-backed lockouts using both normalized-email and normalized-email/IP fingerprints. Redis must be the production cache.

```env
LOGIN_IDENTITY_FAILURE_LIMIT=8
LOGIN_IDENTITY_IP_FAILURE_LIMIT=5
LOGIN_FAILURE_WINDOW_SECONDS=900
LOGIN_LOCKOUT_SECONDS=900
```

Authentication errors remain generic so the mechanism does not reveal whether an account exists.

## Staff MFA

LoveLink includes TOTP MFA for Django Admin accounts. TOTP secrets are encrypted at rest with a key derived from `DJANGO_SECRET_KEY`, and accepted codes cannot be replayed in the same or an older time step.

Enroll each staff account individually:

```bash
docker compose exec backend python manage.py enroll_staff_mfa reviewer@example.com
```

The command prints an `otpauth://` URI once. Add it to Google Authenticator, Microsoft Authenticator, 1Password or another standards-compatible TOTP application. To replace a lost device:

```bash
docker compose exec backend python manage.py enroll_staff_mfa reviewer@example.com --replace
```

After every reviewer, moderator and superuser is enrolled:

```env
STAFF_MFA_REQUIRED=true
STAFF_MFA_ISSUER=LoveLink
```

Changing `DJANGO_SECRET_KEY` without a migration plan makes existing encrypted TOTP secrets unreadable, so rotate it together with re-enrollment or a controlled re-encryption procedure.

## Observability

Structured JSON logs and optional Sentry integration are built in:

```env
LOG_FORMAT=json
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=lovelink@<git-sha>
SENTRY_TRACES_SAMPLE_RATE=0.05
```

Sentry is disabled when the DSN is empty and is configured with default PII collection disabled. Forward JSON stdout/stderr to the platform log system and configure uptime checks for Django `/healthz`, the web application and LiveKit signal/TURN endpoints.

## Local video-call setup

The default `infrastructure/livekit.yaml` uses development credentials and no public TURN certificate. It is only for local Docker development. The browser connects to `ws://localhost:7880`, while Django signs room-specific tokens with the matching local key and secret.

## Production video-call setup

1. Create `rtc.example.com` and `turn.example.com` DNS records pointing to the LiveKit VM.
2. Copy `infrastructure/livekit.prod.yaml.example` to a protected server path.
3. Replace API keys, domains, webhook URL and certificate paths.
4. Expose the signal endpoint as `wss://rtc.example.com` with a trusted certificate.
5. Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` and `NEXT_PUBLIC_LIVEKIT_URL` consistently.
6. Start LiveKit with host networking and mount production configuration and certificates read-only.
7. Verify the signed webhook reaches `/api/v1/webhooks/livekit`.
8. Verify ICE/UDP, ICE/TCP, TURN/UDP and TURN/TLS from real devices and restrictive networks.
9. Verify ringing recovery after reload/WebSocket reconnect.
10. Verify audio-only participation, mobile camera switching and connection-quality changes.

Never commit production keys, OTP provisioning URIs or private certificate files.

## Profile media

- The browser provides an interactive 4:5 crop before upload.
- The backend independently normalizes public profile images to 1200×1500 WebP and creates a 480×600 thumbnail.
- EXIF orientation is applied and metadata is removed during re-encoding.
- Public profile media and private verification evidence use separate buckets and access policies.

## Staff verification workflow

1. Assign each reviewer a unique staff account, enroll MFA and grant `verification.review_verificationrequest`.
2. Open Django Admin → Verification requests.
3. Open a request and use **Mở bằng chứng**. Every access is audited and redirects to a private signed URL valid for five minutes.
4. Use **Bắt đầu xét duyệt** before a final decision.
5. For request-more, reject or revoke, provide a structured reason and user-visible explanation.
6. Approval is blocked unless identity document, selfie and challenge selfie are all present.
7. Every decision creates a review record, notification, optional email and audit entry.

## Moderator workflow

1. Assign `moderation.review_report`, enroll MFA and keep moderator and reviewer permissions separate.
2. Open Django Admin → Reports and inspect the target preview.
3. Choose warn, hide photo/profile, suspend, ban, revoke badge, restore or dismiss.
4. Enter a factual reason and an expiry only for temporary suspension.
5. The action updates state, writes moderation history/audit and sends an account warning where appropriate.

## Notifications and realtime recovery

- Connection emails respect `email_connection_notifications`.
- Message emails respect `email_message_notifications`.
- Unread message notifications are coalesced per conversation for five minutes; only the first item schedules email delivery.
- Verification-result emails respect `email_verification_notifications`.
- Security/account warnings are always eligible for email delivery.
- The WebSocket reconnects automatically. On each successful connection, active chat screens reload through REST to recover missed messages and read markers.

## Scheduled jobs

- Delete expired verification evidence after configured retention.
- Mark unanswered calls as missed.
- Expire stale connection requests.
- Finalize accounts past their deletion grace period.

## Tests

CI runs Django checks, migration drift detection, migrations, backend tests, Python compilation, frontend lint/build and public browser smoke tests. `fullstack-e2e` starts PostgreSQL, Redis, MinIO, Django and Next.js through Docker Compose and validates real session auth, phone OTP, WebSocket chat, read receipts, incoming-call recovery and staff admin screens.

## Backup and recovery

- Back up PostgreSQL with encrypted, access-controlled snapshots and periodic logical dumps.
- Back up public profile media according to the recovery objective.
- Do not retain verification evidence longer than policy; lifecycle deletion must also apply to backups.
- Perform a documented restore drill before public beta and after material infrastructure changes.

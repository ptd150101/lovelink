# Operations

## Production checklist

- Replace all development secrets and pin container-image versions.
- Use HTTPS for app/API/LiveKit and configure trusted origins.
- Configure a production SMTP provider; Celery delivers preference-aware connection, message, verification and security emails.
- Configure a production SMS provider. LoveLink supports Twilio directly; never use the console backend or a fixed OTP code in production.
- Run PostgreSQL and Redis with authentication, backups and restricted networks.
- Put LiveKit on a VM with a public IPv4 and host networking.
- Copy `infrastructure/livekit.prod.yaml.example` outside the repository, replace every placeholder and mount it as the LiveKit config.
- Point the primary RTC domain and the TURN domain to the LiveKit server.
- Terminate HTTPS/WSS for the signal endpoint with a trusted certificate.
- Mount a trusted certificate for the embedded TURN/TLS server.
- Open the configured signal, ICE/TCP, ICE/UDP, TURN/UDP and TURN/TLS ports in both the cloud firewall and host firewall.
- Test calls over normal Wi-Fi, cellular data, a network that blocks UDP and a restrictive corporate network before public beta.
- Configure object-storage lifecycle policies for verification evidence.
- Require MFA for staff accounts and separate reviewer/moderator permissions.
- Add Sentry or equivalent exception monitoring and uptime checks.
- Test database restore and object-storage restore before public beta.
- Review privacy, consent, data-retention, age-gating, phone-number handling and identity-document handling with legal counsel.

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

Login attempts are protected by API throttling plus temporary cache-backed lockouts using both normalized-email and normalized-email/IP fingerprints. Configure Redis as the production cache and review these settings for the expected traffic profile:

```env
# Settings defaults shown; override through deployment settings when needed.
LOGIN_IDENTITY_FAILURE_LIMIT=8
LOGIN_IDENTITY_IP_FAILURE_LIMIT=5
LOGIN_FAILURE_WINDOW_SECONDS=900
LOGIN_LOCKOUT_SECONDS=900
```

Authentication errors remain generic so the lockout mechanism does not reveal whether an account exists.

## Local video-call setup

The default `infrastructure/livekit.yaml` deliberately uses development credentials and no public TURN certificate. It is suitable only for local Docker development. The browser connects to `ws://localhost:7880`, while Django signs room-specific tokens using the matching local key and secret from `.env`.

## Production video-call setup

1. Create `rtc.example.com` and `turn.example.com` DNS records pointing to the LiveKit VM.
2. Copy `infrastructure/livekit.prod.yaml.example` to a protected server path.
3. Replace the API key, secret, domains, webhook URL and certificate paths.
4. Configure the reverse proxy or load balancer to expose the signal endpoint as `wss://rtc.example.com`.
5. Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` and `NEXT_PUBLIC_LIVEKIT_URL` consistently in the application environment.
6. Start LiveKit with host networking and mount the production config plus certificate directory read-only.
7. Verify the signed LiveKit webhook reaches `/api/v1/webhooks/livekit`.
8. Verify ICE/UDP, ICE/TCP, TURN/UDP and TURN/TLS fallbacks from real devices and networks.
9. Verify an incoming ringing call reappears after the callee reloads the tab or reconnects the WebSocket.
10. Verify audio-only participation when camera permission is denied, camera switching on mobile hardware and the connection-quality indicator under degraded networks.

Never commit production keys, secrets or private certificate files.

## Profile media

- The browser provides an interactive 4:5 crop before upload.
- The backend independently normalizes every public profile image to 1200×1500 WebP and creates a 480×600 thumbnail, so clients cannot bypass the aspect-ratio rule.
- EXIF orientation is applied and metadata is removed during re-encoding.
- Public profile media and private verification evidence use separate buckets and access policies.

## Staff verification workflow

1. Assign each reviewer a unique staff account and the `verification.review_verificationrequest` permission.
2. Open Django Admin → Verification requests.
3. Open a request and use the **Mở bằng chứng** buttons. Each access creates an audit entry and redirects to a private signed URL that expires after five minutes.
4. Use **Bắt đầu xét duyệt** before making a final decision.
5. For “request more”, “reject” or “revoke”, fill the reason code and user-visible reason.
6. Use the internal note only for factual staff notes; it is not shown to the member.
7. Approval is blocked unless the identity document, selfie and challenge selfie are all present.
8. Every decision creates a review record, notification, optional preference-aware email and audit-log entry.

## Moderator workflow

1. Assign `moderation.review_report` to each moderator account.
2. Open Django Admin → Reports and inspect the target preview.
3. Choose a structured action: warn, hide photo/profile, suspend, ban, revoke badge, restore or dismiss.
4. Enter a factual reason; add an expiry only for temporary suspension.
5. The action updates the user/profile state, creates a moderation-history row and audit log, and sends an account warning when appropriate.

## Notifications and realtime recovery

- Connection emails respect `email_connection_notifications`.
- Message emails respect `email_message_notifications`.
- Unread message notifications are coalesced per conversation for five minutes, and only the first item in the burst schedules email delivery.
- Verification-result emails respect `email_verification_notifications`.
- Security/account warnings are always eligible for email delivery.
- Celery workers must be running and SMTP credentials must be valid in production.
- The WebSocket reconnects automatically. On each successful connection, active chat screens reload conversation state through REST to recover messages and read markers missed during downtime.

## Scheduled jobs

- Delete expired verification evidence after configured retention.
- Mark unanswered calls as missed.
- Expire stale connection requests.
- Finalize accounts past their deletion grace period.

## Tests

The default CI runs Django checks, migration drift detection, migrations, backend tests, Python compilation, frontend lint/build and public browser smoke tests. The `fullstack-e2e` job additionally starts PostgreSQL, Redis, MinIO, Django and Next.js through Docker Compose and validates real session auth, phone OTP, WebSocket chat, realtime read receipts, incoming-call recovery and staff admin screens.

## Backup and recovery

- Back up PostgreSQL with encrypted, access-controlled snapshots and periodic logical dumps.
- Back up public profile media according to the product recovery objective.
- Do not retain verification evidence longer than the configured policy; lifecycle deletion must also apply to backups.
- Perform a documented restore drill before public beta and after material infrastructure changes.

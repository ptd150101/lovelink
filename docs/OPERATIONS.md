# Operations

## Production checklist

- Replace all development secrets and pin container-image versions.
- Use HTTPS for app/API/LiveKit and configure trusted origins.
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
- Review privacy, consent, data-retention, age-gating and identity-document handling with legal counsel.

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

Never commit production keys, secrets or private certificate files.

## Staff verification workflow

1. Assign each reviewer a unique staff account and the `verification.review_verificationrequest` permission.
2. Open Django Admin → Verification requests.
3. Open each evidence link; links are private signed URLs that expire after five minutes.
4. Start review before making a decision.
5. For “request more”, “reject” or “revoke”, fill `decision_reason_code` and `user_visible_reason` before running the action.
6. Use `internal_note` only for internal factual notes; it is not shown to the member.
7. Approve only after checking the identity document, selfie and challenge selfie.
8. Every decision creates a review record, notification and immutable audit-log entry.

## Scheduled jobs

- Delete expired verification evidence after configured retention.
- Mark unanswered calls as missed.
- Expire stale connection requests.
- Finalize accounts past their deletion grace period.

## Backup and recovery

- Back up PostgreSQL with encrypted, access-controlled snapshots and periodic logical dumps.
- Back up public profile media according to the product recovery objective.
- Do not retain verification evidence longer than the configured policy; lifecycle deletion must also apply to backups.
- Perform a documented restore drill before public beta and after material infrastructure changes.

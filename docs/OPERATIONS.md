# Operations

## Production checklist

- Replace all development secrets and pin container-image versions.
- Use HTTPS for app/API/LiveKit and configure trusted origins.
- Run PostgreSQL and Redis with authentication, backups and restricted networks.
- Put LiveKit on a VM with a public IPv4, open UDP/TCP media ports and validate TURN/fallback behaviour.
- Configure object-storage lifecycle policies for verification evidence.
- Require MFA for staff accounts and separate reviewer/moderator permissions.
- Add Sentry or equivalent exception monitoring and uptime checks.
- Test database restore and object-storage restore before public beta.
- Review privacy, consent, data-retention, age-gating and identity-document handling with legal counsel.

## Scheduled jobs

- Delete expired verification evidence after configured retention.
- Mark unanswered calls as missed.
- Expire stale connection requests.
- Finalize accounts past their deletion grace period.

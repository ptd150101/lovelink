# API overview

All application endpoints are under `/api/v1`. Browser clients use session authentication and CSRF protection.

## Authentication and account

- `GET /auth/csrf`
- `POST /auth/register`
- `POST /auth/email/verify`
- `POST /auth/email/resend`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/password/forgot`
- `POST /auth/password/reset`
- `POST /auth/password/change`
- `GET /auth/sessions`
- `DELETE /auth/sessions/{id}`
- `GET|PATCH /auth/preferences`
- `POST /auth/email/change`
- `POST|DELETE /auth/deletion-request`

Repeated failed logins are temporarily locked by normalized email and email/IP fingerprints while returning the same generic authentication error.

### Phone OTP

- `POST /auth/phone/send`

```json
{"phone":"+84901234567"}
```

Creates a short-lived challenge with a hashed six-digit code, invalidates prior active challenges and applies endpoint rate limits, a resend cooldown and a daily limit.

- `POST /auth/phone/verify`

```json
{"phone":"+84901234567","code":"123456"}
```

The endpoint enforces expiry and attempt limits before atomically assigning the unique private phone number to the current account. Public serializers expose only `is_phone_verified`, never the number.

## Profiles and discovery

- `GET|PATCH /me/profile`
- `POST /me/profile/publish`
- `POST|DELETE /me/profile/hide`
- `/me/photos/*`: presigned upload, completion, reorder, primary-photo selection and delete
- `GET /profiles/{public_id}`
- `GET /discover`

Profile images are cropped by the browser and normalized by the backend to 4:5 WebP derivatives.

Supported discovery query parameters:

- `gender` — repeatable or comma separated
- `min_age`, `max_age`
- `min_height`, `max_height`
- `province`, `hometown`, `occupation`, `education`, `income`, `goal` — repeatable or comma separated
- `verified=true`
- `has_photo=true|false`
- `active_within_days=1..365`
- `sort=recommended|recent|newest|age_asc`
- pagination cursor

## Connections

- `POST /connections/requests`
- `GET /connections/received`
- `GET /connections/sent`
- `GET /connections/accepted`
- `POST /connections/{id}/accept`
- `POST /connections/{id}/decline`
- `POST /connections/{id}/cancel`
- `DELETE /connections/{id}`

## Messaging

- `GET /conversations`
- `GET /conversations/{id}`
- `GET /conversations/{id}/messages`
- `POST /conversations/{id}/messages/send`
- `POST /conversations/{id}/read`

Conversation responses expose `other_last_read_message_id` and `other_last_read_at`. A successful read update emits:

```json
{
  "type":"message.read",
  "payload":{
    "conversation_id":"uuid",
    "reader_public_id":"uuid",
    "message_id":"uuid",
    "read_at":"ISO-8601"
  }
}
```

On every WebSocket connection or reconnect the client reloads the current conversation through REST, deduplicates messages and therefore catches up on events missed while offline.

## Calls

- `POST /calls`
- `GET /calls/incoming`
- `GET /calls/{id}`
- `POST /calls/{id}/accept`
- `POST /calls/{id}/decline`
- `POST /calls/{id}/cancel`
- `POST /calls/{id}/end`
- `POST /calls/{id}/token`
- `POST /webhooks/livekit`

LiveKit tokens are room-specific and short lived. The frontend supports mic/camera toggling, device camera switching, coarse remote connection-quality display and audio-only continuation when camera permission is unavailable.

## Verification and moderation

- `/verification/*`: member identity-verification submissions
- `/staff/verification/*`: reviewer queue and structured actions
- `/blocks`, `/users/{public_id}/block`
- `/reports`
- `/staff/reports/*`: moderator queue and structured actions

Reviewer and moderator workflows are also available through customized Django Admin screens under `/admin/`.

## Notifications

- `GET /notifications`
- `POST /notifications/{id}/read`
- `POST /notifications/read-all`

Notification events are delivered over `/ws/app`. Unread message notifications are coalesced per conversation within a five-minute window, and only the first notification in that burst schedules a delayed email.

## Realtime events

The authenticated WebSocket endpoint is `/ws/app`. Events include connection changes, `message.created`, `message.read`, call lifecycle changes, notification creation/update and account suspension. Pending incoming calls are also recovered through REST after first load and every WebSocket reconnect so ringing state is not lost when a tab reloads.

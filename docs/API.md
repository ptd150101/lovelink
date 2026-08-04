# API overview

All application endpoints are under `/api/v1`. Session authentication and CSRF protection are used for browser clients.

Major resources:

- `/auth/*`: registration, verification/resend, login, logout, password reset/change, preferences and sessions
- `/me/profile`, `/me/photos/*`: profile, privacy, photo ordering and primary-photo management
- `/discover`, `/profiles/{public_id}`: privacy-aware discovery and connection-only coarse presence
- `/connections/*`: intro requests, accepted connections and disconnect
- `/conversations/*`: conversation list, history, send and read
- `/calls/*`: call lifecycle, `GET /calls/incoming` recovery and LiveKit token issuance
- `/verification/*`: identity verification submissions
- `/staff/verification/*`: reviewer queue/actions
- `/blocks`, `/reports`, `/staff/reports/*`: safety and moderation
- `/notifications/*`: notification list/read state; email delivery is handled asynchronously from the same notification event

Realtime events are delivered over `/ws/app`. The frontend recovers pending incoming calls through REST after first load and every WebSocket reconnect so ringing state is not lost when a tab reloads.

Reviewer and moderator workflows are also available through the customized Django Admin under `/admin/`.

# API overview

All application endpoints are under `/api/v1`. Session authentication and CSRF protection are used for browser clients.

Major resources:

- `/auth/*`: registration, verification, login, logout, password reset/change and sessions
- `/me/profile`, `/me/photos/*`: profile and photo management
- `/discover`, `/profiles/{public_id}`: privacy-aware discovery
- `/connections/*`: intro requests and accepted connections
- `/conversations/*`: conversation list, history, send and read
- `/calls/*`: call lifecycle and LiveKit token issuance
- `/verification/*`: identity verification submissions
- `/staff/verification/*`: reviewer queue/actions
- `/blocks`, `/reports`, `/staff/reports/*`: safety and moderation
- `/notifications/*`: notification list/read state

Realtime events are delivered over `/ws/app`.

from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", lambda request: JsonResponse({"status": "ok"})),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.profiles.urls")),
    path("api/v1/", include("apps.connections.urls")),
    path("api/v1/", include("apps.messaging.urls")),
    path("api/v1/", include("apps.calls.urls")),
    path("api/v1/", include("apps.verification.urls")),
    path("api/v1/", include("apps.moderation.urls")),
    path("api/v1/", include("apps.notifications.urls")),
]

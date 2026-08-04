from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from common.realtime import json_safe

from .emails import schedule_notification_email
from .models import Notification
from .serializers import NotificationSerializer


REQUIRED_IN_APP_TYPES = {
    Notification.Type.ACCOUNT_WARNING,
    Notification.Type.VERIFICATION_APPROVED,
    Notification.Type.VERIFICATION_REJECTED,
    Notification.Type.VERIFICATION_NEEDS_MORE,
}


def push_notification(*, user, type, title, body="", actor=None, entity=None):
    preferences = getattr(user, "preferences", None)
    in_app_enabled = (
        preferences is None
        or preferences.in_app_notifications
        or type in REQUIRED_IN_APP_TYPES
    )

    notification = Notification.objects.create(
        user=user,
        type=type,
        title=title,
        body=body,
        actor=actor,
        entity_type=entity.__class__.__name__ if entity else "",
        entity_id=str(entity.pk) if entity else "",
    )

    if in_app_enabled:
        payload = json_safe(NotificationSerializer(notification).data)
        async_to_sync(get_channel_layer().group_send)(
            f"user_{user.pk}",
            {
                "type": "app.event",
                "event": "notification.created",
                "payload": payload,
            },
        )

    schedule_notification_email(notification)
    return notification

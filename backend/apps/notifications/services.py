from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .emails import schedule_notification_email
from .models import Notification
from .serializers import NotificationSerializer


def push_notification(*, user, type, title, body="", actor=None, entity=None):
    preferences = getattr(user, "preferences", None)
    if (
        preferences is not None
        and not preferences.in_app_notifications
        and type
        not in {
            Notification.Type.ACCOUNT_WARNING,
            Notification.Type.VERIFICATION_APPROVED,
            Notification.Type.VERIFICATION_REJECTED,
            Notification.Type.VERIFICATION_NEEDS_MORE,
        }
    ):
        notification = Notification.objects.create(
            user=user,
            type=type,
            title=title,
            body=body,
            actor=actor,
            entity_type=entity.__class__.__name__ if entity else "",
            entity_id=str(entity.pk) if entity else "",
        )
        schedule_notification_email(notification)
        return notification

    notification = Notification.objects.create(
        user=user,
        type=type,
        title=title,
        body=body,
        actor=actor,
        entity_type=entity.__class__.__name__ if entity else "",
        entity_id=str(entity.pk) if entity else "",
    )
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.pk}",
        {
            "type": "app.event",
            "event": "notification.created",
            "payload": NotificationSerializer(notification).data,
        },
    )
    schedule_notification_email(notification)
    return notification

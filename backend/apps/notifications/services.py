from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification
from .serializers import NotificationSerializer

def push_notification(*, user, type, title, body="", actor=None, entity=None):
    notification = Notification.objects.create(
        user=user, type=type, title=title, body=body, actor=actor,
        entity_type=entity.__class__.__name__ if entity else "",
        entity_id=str(entity.pk) if entity else "",
    )
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"user_{user.pk}", {"type": "app.event", "event": "notification.created", "payload": NotificationSerializer(notification).data})
    return notification

from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

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


def _coalesced_message_notification(*, user, title, body, actor, entity):
    if not entity:
        return None
    now = timezone.now()
    window_start = now - timedelta(
        seconds=settings.MESSAGE_NOTIFICATION_COALESCE_SECONDS
    )
    entity_type = entity.__class__.__name__
    entity_id = str(entity.pk)
    notification = (
        Notification.objects.filter(
            user=user,
            type=Notification.Type.MESSAGE_RECEIVED,
            entity_type=entity_type,
            entity_id=entity_id,
            read_at__isnull=True,
            created_at__gte=window_start,
        )
        .order_by("-created_at")
        .first()
    )
    if not notification:
        return None
    Notification.objects.filter(pk=notification.pk).update(
        title=title,
        body=body,
        actor=actor,
        created_at=now,
    )
    notification.refresh_from_db()
    return notification


def push_notification(*, user, type, title, body="", actor=None, entity=None):
    preferences = getattr(user, "preferences", None)
    in_app_enabled = (
        preferences is None
        or preferences.in_app_notifications
        or type in REQUIRED_IN_APP_TYPES
    )

    notification = None
    coalesced = False
    if type == Notification.Type.MESSAGE_RECEIVED:
        notification = _coalesced_message_notification(
            user=user,
            title=title,
            body=body,
            actor=actor,
            entity=entity,
        )
        coalesced = notification is not None

    if notification is None:
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
                "event": (
                    "notification.updated" if coalesced else "notification.created"
                ),
                "payload": payload,
            },
        )

    # Only one delayed email task is needed for a coalesced message burst.
    if not coalesced:
        schedule_notification_email(notification)
    return notification

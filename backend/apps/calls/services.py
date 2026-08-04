from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from livekit import api

from common.realtime import json_safe

from .serializers import CallSessionSerializer


def livekit_token(call, user):
    grants = api.VideoGrants(
        room_join=True,
        room=call.room_name,
        can_publish=True,
        can_subscribe=True,
    )
    return (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(str(user.pk))
        .with_name(user.profile.display_name)
        .with_grants(grants)
        .with_ttl(timedelta(minutes=10))
        .to_jwt()
    )


def call_event(user, event, call):
    payload = json_safe(CallSessionSerializer(call).data)
    async_to_sync(get_channel_layer().group_send)(
        f"user_{user.pk}",
        {
            "type": "app.event",
            "event": event,
            "payload": payload,
        },
    )

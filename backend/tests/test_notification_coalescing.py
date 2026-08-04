import pytest
from django.test import override_settings
from django.utils import timezone

from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation, ConversationMember
from apps.notifications.models import Notification
from apps.notifications.services import push_notification


pytestmark = pytest.mark.django_db


@override_settings(MESSAGE_NOTIFICATION_COALESCE_SECONDS=300)
def test_message_notifications_are_coalesced_per_conversation(user_factory):
    sender = user_factory(email="notify-sender@example.com")
    recipient = user_factory(email="notify-recipient@example.com")
    connection = ConnectionRequest.objects.create(
        sender=sender,
        receiver=recipient,
        intro_message="Xin chào",
        status=ConnectionRequest.Status.ACCEPTED,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )
    conversation = Conversation.objects.create(connection_request=connection)
    ConversationMember.objects.create(conversation=conversation, user=sender)
    ConversationMember.objects.create(conversation=conversation, user=recipient)

    first = push_notification(
        user=recipient,
        type=Notification.Type.MESSAGE_RECEIVED,
        title="Tin nhắn từ Người gửi",
        body="Tin nhắn thứ nhất",
        actor=sender,
        entity=conversation,
    )
    second = push_notification(
        user=recipient,
        type=Notification.Type.MESSAGE_RECEIVED,
        title="Tin nhắn từ Người gửi",
        body="Tin nhắn mới nhất",
        actor=sender,
        entity=conversation,
    )

    assert second.pk == first.pk
    assert Notification.objects.filter(
        user=recipient,
        type=Notification.Type.MESSAGE_RECEIVED,
        entity_id=str(conversation.pk),
    ).count() == 1
    first.refresh_from_db()
    assert first.body == "Tin nhắn mới nhất"

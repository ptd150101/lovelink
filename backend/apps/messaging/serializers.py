from rest_framework import serializers

from apps.connections.serializers import CompactUserSerializer

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_public_id = serializers.UUIDField(
        source="sender.profile.public_id", read_only=True
    )

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender_public_id",
            "client_message_id",
            "message_type",
            "text",
            "created_at",
        )


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "other_user",
            "last_message",
            "last_message_at",
            "unread_count",
            "created_at",
        )

    def _membership(self, obj):
        return next(
            (
                member
                for member in obj.members.all()
                if member.user_id == self.context["request"].user.id
            ),
            None,
        )

    def get_other_user(self, obj):
        other = next(
            (
                member.user
                for member in obj.members.all()
                if member.user_id != self.context["request"].user.id
            ),
            None,
        )
        return (
            CompactUserSerializer(other, context=self.context).data if other else None
        )

    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").first()
        return MessageSerializer(message).data if message else None

    def get_unread_count(self, obj):
        member = self._membership(obj)
        queryset = obj.messages.exclude(sender=self.context["request"].user)
        if member and member.last_read_at:
            queryset = queryset.filter(created_at__gt=member.last_read_at)
        return queryset.count()

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
    other_last_read_message_id = serializers.SerializerMethodField()
    other_last_read_at = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "other_user",
            "last_message",
            "last_message_at",
            "unread_count",
            "other_last_read_message_id",
            "other_last_read_at",
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

    def _other_membership(self, obj):
        return next(
            (
                member
                for member in obj.members.all()
                if member.user_id != self.context["request"].user.id
            ),
            None,
        )

    def get_other_user(self, obj):
        other_member = self._other_membership(obj)
        return (
            CompactUserSerializer(other_member.user, context=self.context).data
            if other_member
            else None
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

    def get_other_last_read_message_id(self, obj):
        other_member = self._other_membership(obj)
        return (
            str(other_member.last_read_message_id)
            if other_member and other_member.last_read_message_id
            else None
        )

    def get_other_last_read_at(self, obj):
        other_member = self._other_membership(obj)
        return other_member.last_read_at if other_member else None

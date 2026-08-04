import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import CursorPagination
from common.throttles import MessageRateThrottle

from .models import Conversation, ConversationMember, Message
from .serializers import ConversationSerializer, MessageSerializer
from .services import send_message


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return (
            Conversation.objects.filter(
                members__user=self.request.user, members__is_hidden=False
            )
            .prefetch_related(
                "members__user__profile__photos",
                "members__last_read_message",
                "messages",
            )
            .order_by("-last_message_at", "-created_at")
        )


class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(
            members__user=self.request.user
        ).prefetch_related(
            "members__user__profile__photos",
            "members__last_read_message",
            "messages",
        )


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = CursorPagination

    def get_queryset(self):
        conversation = get_object_or_404(
            Conversation,
            pk=self.kwargs["pk"],
            members__user=self.request.user,
        )
        return conversation.messages.select_related("sender__profile").order_by(
            "-created_at"
        )


class MessageCreateView(APIView):
    throttle_classes = [MessageRateThrottle]

    def post(self, request, pk):
        conversation = get_object_or_404(
            Conversation, pk=pk, members__user=request.user
        )
        try:
            client_message_id = uuid.UUID(
                str(request.data.get("client_message_id"))
            )
        except Exception:
            return Response(
                {"client_message_id": ["UUID không hợp lệ."]}, status=400
            )
        try:
            message = send_message(
                conversation=conversation,
                user=request.user,
                text=str(request.data.get("text", "")),
                client_message_id=client_message_id,
            )
        except ValueError:
            return Response(
                {"text": ["Tin nhắn cần từ 1 đến 2000 ký tự."]}, status=400
            )
        except PermissionError:
            return Response({"detail": "Không thể gửi tin nhắn."}, status=403)
        return Response(MessageSerializer(message).data, status=201)


class ConversationReadView(APIView):
    def post(self, request, pk):
        with transaction.atomic():
            # Lock only the membership row. Joining nullable relations such as
            # last_read_message while using FOR UPDATE is rejected by PostgreSQL.
            member = get_object_or_404(
                ConversationMember.objects.select_for_update(),
                conversation_id=pk,
                user=request.user,
            )
            requested_id = request.data.get("message_id")
            if requested_id:
                message = get_object_or_404(
                    Message, pk=requested_id, conversation_id=pk
                )
            else:
                message = (
                    Message.objects.filter(conversation_id=pk)
                    .order_by("-created_at")
                    .first()
                )
            if not message:
                return Response(status=204)
            if member.last_read_message_id:
                current_read_at = Message.objects.filter(
                    pk=member.last_read_message_id
                ).values_list("created_at", flat=True).first()
                if current_read_at and current_read_at >= message.created_at:
                    return Response(status=204)
            read_at = timezone.now()
            member.last_read_message = message
            member.last_read_at = read_at
            member.save(update_fields=["last_read_message", "last_read_at"])
            member_ids = list(
                ConversationMember.objects.filter(conversation_id=pk).values_list(
                    "user_id", flat=True
                )
            )

        payload = {
            "conversation_id": str(pk),
            "reader_public_id": str(request.user.profile.public_id),
            "message_id": str(message.pk),
            "read_at": read_at.isoformat(),
        }
        channel_layer = get_channel_layer()
        for user_id in member_ids:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": "app.event",
                    "event": "message.read",
                    "payload": payload,
                },
            )
        return Response(status=204)

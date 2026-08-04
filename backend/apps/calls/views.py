import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import audit
from apps.connections.services import users_are_connected
from apps.messaging.models import Conversation
from apps.moderation.services import are_blocked
from apps.notifications.models import Notification
from apps.notifications.services import push_notification

from .models import CallSession
from .serializers import CallSessionSerializer
from .services import call_event, livekit_token


class CallCreateView(APIView):
    def post(self, request):
        conversation = get_object_or_404(
            Conversation,
            pk=request.data.get("conversation_id"),
            members__user=request.user,
        )
        other_member = (
            conversation.members.exclude(user=request.user)
            .select_related("user")
            .first()
        )
        if (
            not other_member
            or not users_are_connected(request.user, other_member.user)
            or are_blocked(request.user, other_member.user)
        ):
            return Response({"detail": "Không thể gọi người dùng này."}, status=403)
        if (
            CallSession.objects.filter(status__in=CallSession.ACTIVE_STATES)
            .filter(
                Q(caller__in=[request.user, other_member.user])
                | Q(callee__in=[request.user, other_member.user])
            )
            .exists()
        ):
            return Response({"detail": "Một trong hai người đang bận."}, status=409)
        call = CallSession.objects.create(
            room_name=f"call_{uuid.uuid4().hex}",
            caller=request.user,
            callee=other_member.user,
            conversation=conversation,
            status=CallSession.Status.RINGING,
            ringing_at=timezone.now(),
        )
        call_event(other_member.user, "call.incoming", call)
        audit(actor=request.user, action="call.created", target=call)
        return Response(CallSessionSerializer(call).data, status=201)


def participant_call_or_404(user, pk):
    return get_object_or_404(
        CallSession.objects.filter(pk=pk).filter(Q(caller=user) | Q(callee=user))
    )


class IncomingCallView(APIView):
    def get(self, request):
        cutoff = timezone.now() - timezone.timedelta(seconds=30)
        stale = CallSession.objects.filter(
            callee=request.user,
            status=CallSession.Status.RINGING,
            ringing_at__lt=cutoff,
        )
        for call in stale.select_related("caller"):
            call.status = CallSession.Status.MISSED
            call.ended_at = timezone.now()
            call.end_reason = "timeout"
            call.save(update_fields=["status", "ended_at", "end_reason"])
            push_notification(
                user=call.callee,
                type=Notification.Type.CALL_MISSED,
                title="Cuộc gọi nhỡ",
                body=f"{call.caller.profile.display_name} đã gọi cho bạn.",
                actor=call.caller,
                entity=call,
            )
        call = (
            CallSession.objects.filter(
                callee=request.user,
                status=CallSession.Status.RINGING,
                ringing_at__gte=cutoff,
            )
            .select_related("caller__profile", "callee__profile")
            .order_by("-ringing_at")
            .first()
        )
        return Response(
            CallSessionSerializer(call, context={"request": request}).data
            if call
            else None
        )


class CallDetailView(APIView):
    def get(self, request, pk):
        return Response(
            CallSessionSerializer(
                participant_call_or_404(request.user, pk),
                context={"request": request},
            ).data
        )


class CallAcceptView(APIView):
    def post(self, request, pk):
        with transaction.atomic():
            call = get_object_or_404(
                CallSession.objects.select_for_update(), pk=pk, callee=request.user
            )
            if call.status == CallSession.Status.ACCEPTED:
                return Response(
                    {
                        "call": CallSessionSerializer(
                            call, context={"request": request}
                        ).data,
                        "token": livekit_token(call, request.user),
                        "url": settings.LIVEKIT_URL,
                    }
                )
            if call.status != CallSession.Status.RINGING:
                return Response(
                    {"detail": "Cuộc gọi không còn đổ chuông."}, status=409
                )
            call.status = CallSession.Status.ACCEPTED
            call.accepted_at = timezone.now()
            call.save(update_fields=["status", "accepted_at"])
        call_event(call.caller, "call.accepted", call)
        return Response(
            {
                "call": CallSessionSerializer(
                    call, context={"request": request}
                ).data,
                "token": livekit_token(call, request.user),
                "url": settings.LIVEKIT_URL,
            }
        )


class CallTokenView(APIView):
    def post(self, request, pk):
        call = participant_call_or_404(request.user, pk)
        if call.status not in [
            CallSession.Status.ACCEPTED,
            CallSession.Status.CONNECTING,
            CallSession.Status.ACTIVE,
        ]:
            return Response({"detail": "Chưa thể tham gia cuộc gọi."}, status=409)
        return Response(
            {
                "token": livekit_token(call, request.user),
                "url": settings.LIVEKIT_URL,
                "room_name": call.room_name,
            }
        )


class CallDeclineView(APIView):
    def post(self, request, pk):
        call = get_object_or_404(
            CallSession,
            pk=pk,
            callee=request.user,
            status=CallSession.Status.RINGING,
        )
        call.status = CallSession.Status.DECLINED
        call.ended_at = timezone.now()
        call.ended_by = request.user
        call.end_reason = "declined"
        call.save(update_fields=["status", "ended_at", "ended_by", "end_reason"])
        call_event(call.caller, "call.declined", call)
        return Response(CallSessionSerializer(call).data)


class CallCancelView(APIView):
    def post(self, request, pk):
        call = get_object_or_404(
            CallSession,
            pk=pk,
            caller=request.user,
            status=CallSession.Status.RINGING,
        )
        call.status = CallSession.Status.CANCELLED
        call.ended_at = timezone.now()
        call.ended_by = request.user
        call.end_reason = "cancelled"
        call.save(update_fields=["status", "ended_at", "ended_by", "end_reason"])
        call_event(call.callee, "call.cancelled", call)
        return Response(CallSessionSerializer(call).data)


class CallEndView(APIView):
    def post(self, request, pk):
        call = participant_call_or_404(request.user, pk)
        if call.status in [
            CallSession.Status.ENDED,
            CallSession.Status.CANCELLED,
            CallSession.Status.DECLINED,
            CallSession.Status.MISSED,
        ]:
            return Response(CallSessionSerializer(call).data)
        call.status = CallSession.Status.ENDED
        call.ended_at = timezone.now()
        call.ended_by = request.user
        call.end_reason = str(request.data.get("reason", "hangup"))[:100]
        call.save(update_fields=["status", "ended_at", "ended_by", "end_reason"])
        other = call.callee if request.user == call.caller else call.caller
        call_event(other, "call.ended", call)
        return Response(CallSessionSerializer(call).data)


class LiveKitWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            from livekit import api

            receiver = api.WebhookReceiver(
                api.TokenVerifier(
                    settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET
                )
            )
            event = receiver.receive(
                request.body.decode(), request.headers.get("Authorization", "")
            )
        except Exception:
            return Response({"detail": "Invalid webhook"}, status=401)
        room_name = getattr(getattr(event, "room", None), "name", None)
        call = CallSession.objects.filter(room_name=room_name).first()
        if call:
            event_type = str(
                getattr(event, "event", getattr(event, "event_type", ""))
            )
            if "participant_joined" in event_type:
                if not call.connected_at:
                    call.connected_at = timezone.now()
                    call.status = CallSession.Status.ACTIVE
                    call.save(update_fields=["connected_at", "status"])
            elif (
                "room_finished" in event_type
                and call.status in CallSession.ACTIVE_STATES
            ):
                call.status = CallSession.Status.ENDED
                call.ended_at = timezone.now()
                call.end_reason = "room_finished"
                call.save(update_fields=["status", "ended_at", "end_reason"])
        return Response({"ok": True})

from datetime import timedelta
from django.conf import settings
from django.db import IntegrityError,transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.throttles import IntroRateThrottle
from apps.audit.services import audit
from apps.moderation.services import are_blocked
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from apps.profiles.models import Profile
from .models import ConnectionRequest
from .serializers import ConnectionRequestSerializer

class ConnectionCreateView(APIView):
    throttle_classes=[IntroRateThrottle]
    def post(self,request):
        profile=get_object_or_404(Profile,public_id=request.data.get("receiver_public_id"),visibility_status=Profile.Visibility.PUBLISHED,user__status="active")
        receiver=profile.user
        if receiver==request.user:return Response({"detail":"Không thể gửi cho chính mình."},status=400)
        if are_blocked(request.user,receiver):return Response({"detail":"Không thể gửi lời làm quen."},status=403)
        if ConnectionRequest.objects.filter(status=ConnectionRequest.Status.ACCEPTED).filter(sender__in=[request.user,receiver],receiver__in=[request.user,receiver]).exists():return Response({"detail":"Hai bạn đã kết nối."},status=400)
        message=str(request.data.get("intro_message","")).strip()
        if not 1<=len(message)<=300:return Response({"intro_message":["Lời nhắn cần từ 1 đến 300 ký tự."]},status=400)
        if ConnectionRequest.objects.filter(status=ConnectionRequest.Status.PENDING).filter(Q(sender=request.user,receiver=receiver)|Q(sender=receiver,receiver=request.user)).exists():return Response({"detail":"Đã có lời làm quen đang chờ giữa hai bạn."},status=409)
        try:
            obj=ConnectionRequest.objects.create(sender=request.user,receiver=receiver,intro_message=message,expires_at=timezone.now()+timedelta(days=settings.CONNECTION_REQUEST_TTL_DAYS))
        except IntegrityError:return Response({"detail":"Đã có lời làm quen đang chờ."},status=409)
        push_notification(user=receiver,type=Notification.Type.CONNECTION_RECEIVED,title="Bạn có lời làm quen mới",body=f"{request.user.profile.display_name} muốn kết nối với bạn.",actor=request.user,entity=obj)
        audit(actor=request.user,action="connection.requested",target=obj)
        return Response(ConnectionRequestSerializer(obj).data,status=201)

class BaseConnectionList(generics.ListAPIView):serializer_class=ConnectionRequestSerializer
class ReceivedListView(BaseConnectionList):
    def get_queryset(self):return ConnectionRequest.objects.filter(receiver=self.request.user).select_related("sender__profile","receiver__profile")
class SentListView(BaseConnectionList):
    def get_queryset(self):return ConnectionRequest.objects.filter(sender=self.request.user).select_related("sender__profile","receiver__profile")
class AcceptedListView(BaseConnectionList):
    def get_queryset(self):return ConnectionRequest.objects.filter(status=ConnectionRequest.Status.ACCEPTED).filter(Q(sender=self.request.user)|Q(receiver=self.request.user)).select_related("sender__profile","receiver__profile")

class ConnectionAcceptView(APIView):
    def post(self,request,pk):
        with transaction.atomic():
            obj=get_object_or_404(ConnectionRequest.objects.select_for_update(),pk=pk,receiver=request.user)
            if obj.status==ConnectionRequest.Status.ACCEPTED:return Response(ConnectionRequestSerializer(obj).data)
            if obj.status!=ConnectionRequest.Status.PENDING:return Response({"detail":"Yêu cầu không còn chờ phản hồi."},status=409)
            if obj.expires_at<=timezone.now():obj.status=ConnectionRequest.Status.EXPIRED;obj.save(update_fields=["status"]);return Response({"detail":"Yêu cầu đã hết hạn."},status=409)
            if are_blocked(obj.sender,obj.receiver):return Response({"detail":"Không thể kết nối."},status=403)
            obj.status=ConnectionRequest.Status.ACCEPTED;obj.responded_at=timezone.now();obj.save(update_fields=["status","responded_at"])
            from apps.messaging.models import Conversation,ConversationMember
            conversation,_=Conversation.objects.get_or_create(connection_request=obj)
            ConversationMember.objects.get_or_create(conversation=conversation,user=obj.sender);ConversationMember.objects.get_or_create(conversation=conversation,user=obj.receiver)
        push_notification(user=obj.sender,type=Notification.Type.CONNECTION_ACCEPTED,title="Lời làm quen đã được chấp nhận",body=f"{request.user.profile.display_name} đã kết nối với bạn.",actor=request.user,entity=obj)
        audit(actor=request.user,action="connection.accepted",target=obj)
        return Response(ConnectionRequestSerializer(obj).data)

class ConnectionDeclineView(APIView):
    def post(self,request,pk):
        obj=get_object_or_404(ConnectionRequest,pk=pk,receiver=request.user)
        if obj.status!=ConnectionRequest.Status.PENDING:return Response({"detail":"Yêu cầu không còn chờ phản hồi."},status=409)
        obj.status=ConnectionRequest.Status.DECLINED;obj.responded_at=timezone.now();obj.save(update_fields=["status","responded_at"])
        push_notification(user=obj.sender,type=Notification.Type.CONNECTION_DECLINED,title="Lời làm quen chưa được chấp nhận",body="Đối phương đã từ chối lời làm quen.",entity=obj)
        return Response(ConnectionRequestSerializer(obj).data)

class ConnectionCancelView(APIView):
    def post(self,request,pk):
        obj=get_object_or_404(ConnectionRequest,pk=pk,sender=request.user)
        if obj.status!=ConnectionRequest.Status.PENDING:return Response({"detail":"Yêu cầu không thể hủy."},status=409)
        obj.status=ConnectionRequest.Status.CANCELLED;obj.responded_at=timezone.now();obj.save(update_fields=["status","responded_at"])
        return Response(ConnectionRequestSerializer(obj).data)

class ConnectionDeleteView(APIView):
    def delete(self,request,pk):
        obj=get_object_or_404(ConnectionRequest,pk=pk,status=ConnectionRequest.Status.ACCEPTED)
        if request.user.id not in {obj.sender_id,obj.receiver_id}:return Response(status=403)
        obj.status=ConnectionRequest.Status.CANCELLED;obj.responded_at=timezone.now();obj.save(update_fields=["status","responded_at"])
        if hasattr(obj,"conversation"):obj.conversation.members.update(is_hidden=True)
        return Response(status=204)

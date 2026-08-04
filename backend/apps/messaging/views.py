import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.pagination import CursorPagination
from common.throttles import MessageRateThrottle
from .models import Conversation,ConversationMember,Message
from .serializers import ConversationSerializer,MessageSerializer
from .services import send_message

class ConversationListView(generics.ListAPIView):
 serializer_class=ConversationSerializer
 def get_queryset(self):return Conversation.objects.filter(members__user=self.request.user,members__is_hidden=False).prefetch_related("members__user__profile__photos","messages").order_by("-last_message_at","-created_at")

class ConversationDetailView(generics.RetrieveAPIView):
 serializer_class=ConversationSerializer
 def get_queryset(self):return Conversation.objects.filter(members__user=self.request.user).prefetch_related("members__user__profile__photos","messages")

class MessageListView(generics.ListAPIView):
 serializer_class=MessageSerializer
 pagination_class=CursorPagination
 def get_queryset(self):
  c=get_object_or_404(Conversation,pk=self.kwargs["pk"],members__user=self.request.user);return c.messages.select_related("sender__profile").order_by("-created_at")

class MessageCreateView(APIView):
 throttle_classes=[MessageRateThrottle]
 def post(self,request,pk):
  c=get_object_or_404(Conversation,pk=pk,members__user=request.user)
  try:cid=uuid.UUID(str(request.data.get("client_message_id")))
  except Exception:return Response({"client_message_id":["UUID không hợp lệ."]},status=400)
  try:m=send_message(conversation=c,user=request.user,text=str(request.data.get("text","")),client_message_id=cid)
  except ValueError:return Response({"text":["Tin nhắn cần từ 1 đến 2000 ký tự."]},status=400)
  except PermissionError:return Response({"detail":"Không thể gửi tin nhắn."},status=403)
  return Response(MessageSerializer(m).data,status=201)

class ConversationReadView(APIView):
 def post(self,request,pk):
  member=get_object_or_404(ConversationMember,conversation_id=pk,user=request.user);message=None
  if request.data.get("message_id"):message=get_object_or_404(Message,pk=request.data["message_id"],conversation_id=pk)
  else:message=Message.objects.filter(conversation_id=pk).order_by("-created_at").first()
  member.last_read_message=message;member.last_read_at=timezone.now();member.save(update_fields=["last_read_message","last_read_at"])
  return Response(status=204)

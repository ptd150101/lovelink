import uuid
from django.conf import settings
from django.db import models
class CallSession(models.Model):
 class Status(models.TextChoices):CREATED="created","Đã tạo";RINGING="ringing","Đang đổ chuông";ACCEPTED="accepted","Đã nhận";CONNECTING="connecting","Đang kết nối";ACTIVE="active","Đang gọi";DECLINED="declined","Từ chối";CANCELLED="cancelled","Đã hủy";MISSED="missed","Cuộc gọi nhỡ";ENDED="ended","Đã kết thúc";FAILED="failed","Lỗi"
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 room_name=models.CharField(max_length=160,unique=True)
 caller=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="outgoing_calls")
 callee=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="incoming_calls")
 conversation=models.ForeignKey("messaging.Conversation",on_delete=models.CASCADE,related_name="calls")
 call_type=models.CharField(max_length=12,default="video")
 status=models.CharField(max_length=16,choices=Status.choices,default=Status.CREATED,db_index=True)
 created_at=models.DateTimeField(auto_now_add=True)
 ringing_at=models.DateTimeField(null=True,blank=True)
 accepted_at=models.DateTimeField(null=True,blank=True)
 connected_at=models.DateTimeField(null=True,blank=True)
 ended_at=models.DateTimeField(null=True,blank=True)
 ended_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="ended_calls")
 end_reason=models.CharField(max_length=100,blank=True)
 ACTIVE_STATES=[Status.CREATED,Status.RINGING,Status.ACCEPTED,Status.CONNECTING,Status.ACTIVE]
 class Meta:indexes=[models.Index(fields=["caller","status"]),models.Index(fields=["callee","status"])]

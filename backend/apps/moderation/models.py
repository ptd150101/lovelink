import uuid
from django.conf import settings
from django.db import models

class Block(models.Model):
    blocker=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="blocks_created")
    blocked=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="blocks_received")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["blocker","blocked"],name="unique_block_pair"),models.CheckConstraint(condition=~models.Q(blocker=models.F("blocked")),name="blocker_not_blocked")]

class Report(models.Model):
    class Target(models.TextChoices):PROFILE="profile","Hồ sơ"; MESSAGE="message","Tin nhắn"; CALL="call","Cuộc gọi"; PHOTO="photo","Ảnh"
    class Reason(models.TextChoices):FAKE="fake","Giả mạo"; SCAM="scam","Lừa đảo"; HARASSMENT="harassment","Quấy rối"; SEXUAL="sexual","Nội dung tình dục"; THREAT="threat","Đe dọa"; SPAM="spam","Spam"; UNDERAGE="underage","Chưa đủ tuổi"; WRONG_PHOTO="wrong_photo","Ảnh không chính chủ"; OTHER="other","Khác"
    class Status(models.TextChoices):OPEN="open","Mới"; IN_REVIEW="in_review","Đang xử lý"; ACTION="action_taken","Đã xử lý"; DISMISSED="dismissed","Bỏ qua"; ESCALATED="escalated","Chuyển cấp"
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    reporter=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name="reports_created")
    reported_user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="reports_received")
    target_type=models.CharField(max_length=20,choices=Target.choices)
    target_id=models.CharField(max_length=128)
    reason_code=models.CharField(max_length=32,choices=Reason.choices)
    description=models.TextField(blank=True,max_length=2000)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.OPEN,db_index=True)
    assigned_moderator=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="assigned_reports")
    resolution=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    resolved_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        permissions=[("review_report","Can review user reports")]
        indexes=[models.Index(fields=["status","created_at"])]

class ModerationAction(models.Model):
    class Action(models.TextChoices):WARN="warn","Cảnh báo"; HIDE_PHOTO="hide_photo","Ẩn ảnh"; HIDE_PROFILE="hide_profile","Ẩn hồ sơ"; SUSPEND="suspend","Đình chỉ"; BAN="ban","Cấm"; REVOKE_BADGE="revoke_badge","Thu hồi tích xanh"; RESTORE="restore","Khôi phục"
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    moderator=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="moderation_actions")
    target_user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="moderation_history")
    report=models.ForeignKey(Report,null=True,blank=True,on_delete=models.SET_NULL,related_name="actions")
    action=models.CharField(max_length=32,choices=Action.choices)
    reason=models.TextField()
    expires_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

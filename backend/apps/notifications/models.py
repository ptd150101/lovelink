import uuid
from django.conf import settings
from django.db import models

class Notification(models.Model):
    class Type(models.TextChoices):
        CONNECTION_RECEIVED = "connection.received", "Lời làm quen mới"
        CONNECTION_ACCEPTED = "connection.accepted", "Kết nối được chấp nhận"
        CONNECTION_DECLINED = "connection.declined", "Lời làm quen bị từ chối"
        MESSAGE_RECEIVED = "message.received", "Tin nhắn mới"
        CALL_MISSED = "call.missed", "Cuộc gọi nhỡ"
        VERIFICATION_SUBMITTED = "verification.submitted", "Đã gửi xác minh"
        VERIFICATION_NEEDS_MORE = "verification.needs_more_info", "Cần bổ sung xác minh"
        VERIFICATION_APPROVED = "verification.approved", "Xác minh thành công"
        VERIFICATION_REJECTED = "verification.rejected", "Xác minh bị từ chối"
        ACCOUNT_WARNING = "account.warning", "Cảnh báo tài khoản"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=64, choices=Type.choices, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="triggered_notifications")
    entity_type = models.CharField(max_length=64, blank=True)
    entity_id = models.CharField(max_length=128, blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at", "-created_at"])]

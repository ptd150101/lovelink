import uuid
from django.conf import settings
from django.db import models

class ConnectionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING="pending","Chờ phản hồi"; ACCEPTED="accepted","Đã kết nối"; DECLINED="declined","Đã từ chối"; CANCELLED="cancelled","Đã hủy"; EXPIRED="expired","Hết hạn"; BLOCKED="blocked","Đã chặn"
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="sent_connection_requests")
    receiver=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="received_connection_requests")
    pair_key=models.CharField(max_length=73,db_index=True)
    intro_message=models.CharField(max_length=300)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PENDING,db_index=True)
    sent_at=models.DateTimeField(auto_now_add=True,db_index=True)
    responded_at=models.DateTimeField(null=True,blank=True)
    expires_at=models.DateTimeField(db_index=True)
    class Meta:
        ordering=("-sent_at",)
        constraints=[
            models.CheckConstraint(condition=~models.Q(sender=models.F("receiver")),name="connection_sender_not_receiver"),
            models.UniqueConstraint(fields=["pair_key"],condition=models.Q(status="pending"),name="unique_pending_connection_pair"),
        ]
        indexes=[models.Index(fields=["receiver","status","-sent_at"]),models.Index(fields=["sender","status","-sent_at"])]
    def save(self,*args,**kwargs):
        self.pair_key="|".join(sorted([str(self.sender_id),str(self.receiver_id)]))
        super().save(*args,**kwargs)

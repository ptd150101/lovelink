import uuid
from django.conf import settings
from django.db import models

class Conversation(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    connection_request=models.OneToOneField("connections.ConnectionRequest",on_delete=models.PROTECT,related_name="conversation")
    created_at=models.DateTimeField(auto_now_add=True)
    last_message_at=models.DateTimeField(null=True,blank=True,db_index=True)

class ConversationMember(models.Model):
    conversation=models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name="members")
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="conversation_memberships")
    last_read_message=models.ForeignKey("Message",null=True,blank=True,on_delete=models.SET_NULL,related_name="read_markers")
    last_read_at=models.DateTimeField(null=True,blank=True)
    is_hidden=models.BooleanField(default=False)
    class Meta:constraints=[models.UniqueConstraint(fields=["conversation","user"],name="unique_conversation_member")]

class Message(models.Model):
    class Type(models.TextChoices):TEXT="text","Văn bản";SYSTEM="system","Hệ thống"
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    conversation=models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name="messages")
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="sent_messages")
    client_message_id=models.UUIDField()
    message_type=models.CharField(max_length=16,choices=Type.choices,default=Type.TEXT)
    text=models.CharField(max_length=2000)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    deleted_for_sender_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=("created_at",);constraints=[models.UniqueConstraint(fields=["sender","client_message_id"],name="unique_client_message_per_sender")];indexes=[models.Index(fields=["conversation","-created_at"])]

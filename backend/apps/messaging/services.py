from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import IntegrityError,transaction
from django.utils import timezone
from apps.moderation.services import are_blocked
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from .models import ConversationMember,Message
from .serializers import MessageSerializer

def send_message(*,conversation,user,text,client_message_id):
    membership=ConversationMember.objects.filter(conversation=conversation,user=user).select_related("conversation__connection_request").first()
    if not membership:raise PermissionError("Not a member")
    other=ConversationMember.objects.filter(conversation=conversation).exclude(user=user).select_related("user").first()
    if not other or are_blocked(user,other.user):raise PermissionError("Blocked")
    if conversation.connection_request.status!="accepted":raise PermissionError("Connection inactive")
    text=text.strip()
    if not 1<=len(text)<=2000:raise ValueError("Invalid message length")
    try:
        with transaction.atomic():
            message=Message.objects.create(conversation=conversation,sender=user,text=text,client_message_id=client_message_id)
            conversation.last_message_at=message.created_at;conversation.save(update_fields=["last_message_at"])
            membership.is_hidden=False;membership.save(update_fields=["is_hidden"]);other.is_hidden=False;other.save(update_fields=["is_hidden"])
    except IntegrityError:message=Message.objects.get(sender=user,client_message_id=client_message_id)
    payload=MessageSerializer(message).data;layer=get_channel_layer()
    for member in conversation.members.all():async_to_sync(layer.group_send)(f"user_{member.user_id}",{"type":"app.event","event":"message.created","payload":payload})
    push_notification(user=other.user,type=Notification.Type.MESSAGE_RECEIVED,title=f"Tin nhắn từ {user.profile.display_name}",body=text[:120],actor=user,entity=conversation)
    return message

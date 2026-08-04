import uuid
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

class AppConsumer(AsyncJsonWebsocketConsumer):
 async def connect(self):
  user=self.scope["user"]
  if not user.is_authenticated or user.status!="active":await self.close(code=4401);return
  self.user=user;self.group=f"user_{user.pk}";await self.channel_layer.group_add(self.group,self.channel_name);await self.accept();await self.send_json({"type":"ready"})
 async def disconnect(self,code):
  if hasattr(self,"group"):await self.channel_layer.group_discard(self.group,self.channel_name)
 async def receive_json(self,content,**kwargs):
  t=content.get("type")
  if t=="presence.ping":await self.touch_presence();await self.send_json({"type":"presence.pong"})
  elif t=="message.read":await self.mark_read(content.get("conversation_id"),content.get("message_id"))
  else:await self.send_json({"type":"error","code":"unsupported_event"})
 async def app_event(self,event):await self.send_json({"type":event["event"],"payload":event.get("payload",{})})
 @database_sync_to_async
 def touch_presence(self):
  self.user.last_seen_at=timezone.now();self.user.save(update_fields=["last_seen_at"])
 @database_sync_to_async
 def mark_read(self,conversation_id,message_id):
  from .models import ConversationMember,Message
  try:member=ConversationMember.objects.get(conversation_id=conversation_id,user=self.user);message=Message.objects.get(pk=message_id,conversation_id=conversation_id);member.last_read_message=message;member.last_read_at=timezone.now();member.save(update_fields=["last_read_message","last_read_at"])
  except (ConversationMember.DoesNotExist,Message.DoesNotExist,ValueError):pass

import uuid,pytest
from django.utils import timezone
from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation
from apps.moderation.models import Block

@pytest.mark.django_db
def test_accept_connection_creates_single_conversation(api_client,user_factory):
 a=user_factory("a@example.com");b=user_factory("b@example.com")
 req=ConnectionRequest.objects.create(sender=a,receiver=b,intro_message="Xin chào",expires_at=timezone.now()+timezone.timedelta(days=1))
 api_client.force_authenticate(b);r=api_client.post(f"/api/v1/connections/{req.id}/accept")
 assert r.status_code==200 and Conversation.objects.filter(connection_request=req).count()==1
 r2=api_client.post(f"/api/v1/connections/{req.id}/accept")
 assert r2.status_code==200 and Conversation.objects.filter(connection_request=req).count()==1

@pytest.mark.django_db
def test_message_requires_membership_and_block_check(api_client,user_factory):
 a=user_factory("a@example.com");b=user_factory("b@example.com");c=user_factory("c@example.com")
 req=ConnectionRequest.objects.create(sender=a,receiver=b,intro_message="Xin chào",status=ConnectionRequest.Status.ACCEPTED,expires_at=timezone.now()+timezone.timedelta(days=1))
 from apps.messaging.models import ConversationMember
 conv=Conversation.objects.create(connection_request=req);ConversationMember.objects.create(conversation=conv,user=a);ConversationMember.objects.create(conversation=conv,user=b)
 api_client.force_authenticate(c);r=api_client.post(f"/api/v1/conversations/{conv.id}/messages/send",{"client_message_id":str(uuid.uuid4()),"text":"hello"},format="json");assert r.status_code==404
 Block.objects.create(blocker=b,blocked=a);api_client.force_authenticate(a);r=api_client.post(f"/api/v1/conversations/{conv.id}/messages/send",{"client_message_id":str(uuid.uuid4()),"text":"hello"},format="json");assert r.status_code==403

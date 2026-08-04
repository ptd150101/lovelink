import pytest
from django.contrib.auth.models import Permission
from django.utils import timezone
from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation,ConversationMember
from apps.verification.models import VerificationRequest,VerificationEvidence

@pytest.mark.django_db
def test_call_requires_accepted_connection(api_client,user_factory):
 a=user_factory("a@example.com");b=user_factory("b@example.com")
 req=ConnectionRequest.objects.create(sender=a,receiver=b,intro_message="x",status=ConnectionRequest.Status.ACCEPTED,expires_at=timezone.now()+timezone.timedelta(days=1))
 conv=Conversation.objects.create(connection_request=req);ConversationMember.objects.create(conversation=conv,user=a);ConversationMember.objects.create(conversation=conv,user=b)
 api_client.force_authenticate(a);r=api_client.post("/api/v1/calls",{"conversation_id":str(conv.id)},format="json")
 assert r.status_code==201 and r.data["status"]=="ringing"

@pytest.mark.django_db
def test_reviewer_approval_sets_badge(api_client,user_factory):
 user=user_factory("member@example.com");reviewer=user_factory("reviewer@example.com");reviewer.is_staff=True;reviewer.save(update_fields=["is_staff"])
 reviewer.user_permissions.add(Permission.objects.get(codename="review_verificationrequest"))
 vr=VerificationRequest.objects.create(user=user,status=VerificationRequest.Status.SUBMITTED,challenge_code="ABC123",submitted_at=timezone.now())
 api_client.force_authenticate(reviewer);r=api_client.post(f"/api/v1/staff/verification/{vr.id}/action",{"action":"approve"},format="json")
 user.profile.refresh_from_db();assert r.status_code==200 and user.profile.verification_level=="identity_verified"

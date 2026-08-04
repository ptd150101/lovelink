import pytest
from django.contrib.auth.models import Permission
from django.utils import timezone

from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation, ConversationMember
from apps.verification.models import VerificationEvidence, VerificationRequest


@pytest.mark.django_db
def test_call_requires_accepted_connection(api_client, user_factory):
    first = user_factory("a@example.com")
    second = user_factory("b@example.com")
    connection = ConnectionRequest.objects.create(
        sender=first,
        receiver=second,
        intro_message="x",
        status=ConnectionRequest.Status.ACCEPTED,
        expires_at=timezone.now() + timezone.timedelta(days=1),
    )
    conversation = Conversation.objects.create(connection_request=connection)
    ConversationMember.objects.create(conversation=conversation, user=first)
    ConversationMember.objects.create(conversation=conversation, user=second)
    api_client.force_authenticate(first)
    response = api_client.post(
        "/api/v1/calls", {"conversation_id": str(conversation.id)}, format="json"
    )
    assert response.status_code == 201
    assert response.data["status"] == "ringing"


@pytest.mark.django_db
def test_reviewer_approval_sets_badge(api_client, user_factory):
    user = user_factory("member@example.com")
    reviewer = user_factory("reviewer@example.com")
    reviewer.is_staff = True
    reviewer.save(update_fields=["is_staff"])
    reviewer.user_permissions.add(
        Permission.objects.get(codename="review_verificationrequest")
    )
    verification = VerificationRequest.objects.create(
        user=user,
        status=VerificationRequest.Status.SUBMITTED,
        challenge_code="ABC123",
        submitted_at=timezone.now(),
    )
    for evidence_type in VerificationEvidence.Type.values:
        VerificationEvidence.objects.create(
            request=verification,
            evidence_type=evidence_type,
            private_object_key=f"verification/tests/{evidence_type}.webp",
            mime_type="image/webp",
            file_size=100,
        )
    api_client.force_authenticate(reviewer)
    response = api_client.post(
        f"/api/v1/staff/verification/{verification.id}/action",
        {"action": "approve"},
        format="json",
    )
    user.profile.refresh_from_db()
    assert response.status_code == 200
    assert user.profile.verification_level == "identity_verified"

import uuid

import pytest
from django.contrib import mail
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserPreference
from apps.calls.models import CallSession
from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation, ConversationMember
from apps.moderation.models import Report
from apps.notifications.models import Notification
from apps.notifications.tasks import send_notification_email
from apps.profiles.models import Profile
from apps.verification.models import VerificationEvidence, VerificationRequest


pytestmark = pytest.mark.django_db


def accepted_conversation(first, second):
    request = ConnectionRequest.objects.create(
        sender=first,
        receiver=second,
        intro_message="Xin chào",
        status=ConnectionRequest.Status.ACCEPTED,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )
    conversation = Conversation.objects.create(connection_request=request)
    ConversationMember.objects.create(conversation=conversation, user=first)
    ConversationMember.objects.create(conversation=conversation, user=second)
    return conversation


def test_presence_respects_connection_and_privacy(api_client, user_factory):
    viewer = user_factory(email="viewer@example.com", gender=Profile.Gender.MALE)
    target = user_factory(
        email="target@example.com",
        gender=Profile.Gender.FEMALE,
        interested_genders=[Profile.Gender.MALE],
    )
    viewer.profile.visibility_status = Profile.Visibility.PUBLISHED
    viewer.profile.save(update_fields=["visibility_status"])
    target.profile.visibility_status = Profile.Visibility.PUBLISHED
    target.profile.save(update_fields=["visibility_status"])
    accepted_conversation(viewer, target)
    target.last_seen_at = timezone.now()
    target.save(update_fields=["last_seen_at"])

    api_client.force_authenticate(viewer)
    response = api_client.get(f"/api/v1/profiles/{target.profile.public_id}")
    assert response.status_code == 200
    assert response.data["presence"] == {"status": "online"}

    preferences, _ = UserPreference.objects.get_or_create(user=target)
    preferences.show_online_status = False
    preferences.save(update_fields=["show_online_status"])
    response = api_client.get(f"/api/v1/profiles/{target.profile.public_id}")
    assert response.data["presence"] is None


def test_incoming_call_can_be_recovered_after_reload(api_client, user_factory):
    caller = user_factory(email="caller@example.com", gender=Profile.Gender.MALE)
    callee = user_factory(email="callee@example.com", gender=Profile.Gender.FEMALE)
    conversation = accepted_conversation(caller, callee)
    call = CallSession.objects.create(
        room_name=f"call_{uuid.uuid4().hex}",
        caller=caller,
        callee=callee,
        conversation=conversation,
        status=CallSession.Status.RINGING,
        ringing_at=timezone.now(),
    )
    api_client.force_authenticate(callee)
    response = api_client.get("/api/v1/calls/incoming")
    assert response.status_code == 200
    assert response.data["id"] == str(call.pk)


def test_notification_email_honors_preference(user_factory):
    user = user_factory(email="mail@example.com")
    preferences, _ = UserPreference.objects.get_or_create(user=user)
    preferences.email_connection_notifications = True
    preferences.save(update_fields=["email_connection_notifications"])
    notification = Notification.objects.create(
        user=user,
        type=Notification.Type.CONNECTION_RECEIVED,
        title="Lời làm quen mới",
        body="Bạn có một lời làm quen.",
    )
    assert send_notification_email(str(notification.pk)) is True
    assert len(mail.outbox) == 1
    assert "Lời làm quen mới" in mail.outbox[0].subject

    mail.outbox.clear()
    preferences.email_connection_notifications = False
    preferences.save(update_fields=["email_connection_notifications"])
    assert send_notification_email(str(notification.pk)) is False
    assert mail.outbox == []


def test_custom_staff_admin_workflows(client, user_factory):
    member = user_factory(email="reviewed@example.com")
    reviewer = User.objects.create_superuser(
        email="admin@example.com", password="StrongAdminPassword123!"
    )
    verification = VerificationRequest.objects.create(
        user=member,
        status=VerificationRequest.Status.SUBMITTED,
        challenge_code="ABC123",
        submitted_at=timezone.now(),
    )
    for evidence_type in VerificationEvidence.Type.values:
        VerificationEvidence.objects.create(
            request=verification,
            evidence_type=evidence_type,
            private_object_key=f"verification/test/{evidence_type}.webp",
            mime_type="image/webp",
            file_size=100,
        )
    report = Report.objects.create(
        reporter=reviewer,
        reported_user=member,
        target_type=Report.Target.PROFILE,
        target_id=str(member.profile.public_id),
        reason_code=Report.Reason.FAKE,
        description="Kiểm tra giao diện moderator.",
    )
    client.force_login(reviewer)

    verification_change = reverse(
        "admin:verification_verificationrequest_change", args=[verification.pk]
    )
    response = client.get(verification_change)
    assert response.status_code == 200
    assert "Thao tác xét duyệt" in response.content.decode()
    response = client.post(
        reverse(
            "admin:verification_verificationrequest_review", args=[verification.pk]
        ),
        {"review_action": "approve"},
        follow=True,
    )
    assert response.status_code == 200
    member.profile.refresh_from_db()
    assert member.profile.verification_level == Profile.VerificationLevel.IDENTITY

    report_change = reverse("admin:moderation_report_change", args=[report.pk])
    response = client.get(report_change)
    assert response.status_code == 200
    assert "Xử lý báo cáo" in response.content.decode()
    response = client.post(
        reverse("admin:moderation_report_moderate", args=[report.pk]),
        {"moderation_action": "warn", "reason": "Cảnh báo thử nghiệm"},
        follow=True,
    )
    assert response.status_code == 200
    report.refresh_from_db()
    assert report.status == Report.Status.ACTION

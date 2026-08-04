import pytest
from django.contrib.auth.models import Permission
from django.utils import timezone
from apps.accounts.models import UserPreference
from apps.moderation.models import Block, Report
from apps.notifications.models import Notification
from apps.profiles.models import Profile, ProfilePhoto
from apps.verification.models import VerificationRequest

@pytest.mark.django_db
def test_user_can_update_notification_preferences(api_client, user_factory):
    user = user_factory("prefs@example.com")
    api_client.force_authenticate(user)
    response = api_client.patch("/api/v1/auth/preferences", {"email_message_notifications": True, "show_online_status": False}, format="json")
    assert response.status_code == 200
    preference = UserPreference.objects.get(user=user)
    assert preference.email_message_notifications is True
    assert preference.show_online_status is False

@pytest.mark.django_db
def test_block_hides_profile_and_prevents_direct_access(api_client, user_factory):
    a = user_factory("a@example.com", gender=Profile.Gender.MALE, interested_genders=[Profile.Gender.FEMALE])
    b = user_factory("b@example.com", gender=Profile.Gender.FEMALE, interested_genders=[Profile.Gender.MALE])
    b.profile.visibility_status = Profile.Visibility.PUBLISHED
    b.profile.save(update_fields=["visibility_status"])
    ProfilePhoto.objects.create(profile=b.profile, object_key="b.webp", public_url="https://example/b.webp", is_primary=True, mime_type="image/webp")
    Block.objects.create(blocker=a, blocked=b)
    api_client.force_authenticate(a)
    assert api_client.get(f"/api/v1/profiles/{b.profile.public_id}").status_code == 404

@pytest.mark.django_db
def test_report_duplicate_is_rejected(api_client, user_factory):
    a = user_factory("reporter@example.com")
    b = user_factory("reported@example.com")
    api_client.force_authenticate(a)
    payload = {"reported_user_public_id": str(b.profile.public_id), "target_type": "profile", "target_id": str(b.profile.public_id), "reason_code": "fake", "description": "Nghi ngờ giả mạo"}
    assert api_client.post("/api/v1/reports", payload, format="json").status_code == 201
    assert api_client.post("/api/v1/reports", payload, format="json").status_code == 409

@pytest.mark.django_db
def test_verification_reject_requires_visible_reason(api_client, user_factory):
    member = user_factory("member@example.com")
    reviewer = user_factory("reviewer@example.com")
    reviewer.is_staff = True
    reviewer.save(update_fields=["is_staff"])
    reviewer.user_permissions.add(Permission.objects.get(codename="review_verificationrequest"))
    request = VerificationRequest.objects.create(user=member, status=VerificationRequest.Status.SUBMITTED, challenge_code="ABC123", submitted_at=timezone.now())
    api_client.force_authenticate(reviewer)
    response = api_client.post(f"/api/v1/staff/verification/{request.id}/action", {"action": "reject"}, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_notification_can_be_marked_read(api_client, user_factory):
    user = user_factory("notify@example.com")
    notification = Notification.objects.create(user=user, type=Notification.Type.ACCOUNT_WARNING, title="Cảnh báo")
    api_client.force_authenticate(user)
    response = api_client.post(f"/api/v1/notifications/{notification.id}/read")
    notification.refresh_from_db()
    assert response.status_code == 200
    assert notification.read_at is not None

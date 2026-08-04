from io import BytesIO

import pytest
from django.test import override_settings
from django.utils import timezone
from PIL import Image

from apps.accounts.models import PhoneVerificationChallenge
from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation, ConversationMember, Message
from apps.profiles import image_processing
from apps.profiles.models import Profile, ProfilePhoto


pytestmark = pytest.mark.django_db


def accepted_conversation(first, second):
    connection = ConnectionRequest.objects.create(
        sender=first,
        receiver=second,
        intro_message="Xin chào",
        status=ConnectionRequest.Status.ACCEPTED,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )
    conversation = Conversation.objects.create(connection_request=connection)
    ConversationMember.objects.create(conversation=conversation, user=first)
    ConversationMember.objects.create(conversation=conversation, user=second)
    return conversation


@override_settings(
    SMS_BACKEND="console",
    PHONE_OTP_FIXED_CODE="123456",
    PHONE_OTP_RESEND_SECONDS=0,
    PHONE_OTP_DAILY_LIMIT=5,
    PHONE_OTP_MAX_ATTEMPTS=3,
)
def test_phone_otp_verifies_and_replaces_phone(api_client, user_factory):
    user = user_factory(email="phone@example.com")
    api_client.force_authenticate(user)

    response = api_client.post(
        "/api/v1/auth/phone/send", {"phone": "0901 234 567"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["phone"].startswith("+84")
    challenge = PhoneVerificationChallenge.objects.get(user=user)
    assert challenge.phone == "+84901234567"
    assert challenge.code_hash != "123456"

    wrong = api_client.post(
        "/api/v1/auth/phone/verify",
        {"phone": "+84901234567", "code": "000000"},
        format="json",
    )
    assert wrong.status_code == 400
    assert wrong.data["attempts_remaining"] == 2

    verified = api_client.post(
        "/api/v1/auth/phone/verify",
        {"phone": "+84901234567", "code": "123456"},
        format="json",
    )
    assert verified.status_code == 200
    assert verified.data["is_phone_verified"] is True
    assert verified.data["phone"] == "+84901234567"
    user.refresh_from_db()
    assert user.is_phone_verified is True
    assert user.phone == "+84901234567"
    challenge.refresh_from_db()
    assert challenge.consumed_at is not None


@override_settings(
    SMS_BACKEND="console",
    PHONE_OTP_FIXED_CODE="123456",
    PHONE_OTP_RESEND_SECONDS=0,
)
def test_phone_otp_rejects_duplicate_phone(api_client, user_factory):
    existing = user_factory(email="existing-phone@example.com")
    existing.phone = "+84909999999"
    existing.is_phone_verified = True
    existing.save(update_fields=["phone", "is_phone_verified"])
    user = user_factory(email="new-phone@example.com")
    api_client.force_authenticate(user)

    response = api_client.post(
        "/api/v1/auth/phone/send",
        {"phone": "+84909999999"},
        format="json",
    )
    assert response.status_code == 400
    assert "phone" in response.data
    assert not PhoneVerificationChallenge.objects.filter(user=user).exists()


def test_discovery_filters_photo_activity_and_gender(api_client, user_factory):
    viewer = user_factory(
        email="filter-viewer@example.com",
        gender=Profile.Gender.MALE,
        interested_genders=[Profile.Gender.FEMALE],
    )
    active_with_photo = user_factory(
        email="active-photo@example.com",
        gender=Profile.Gender.FEMALE,
        interested_genders=[Profile.Gender.MALE],
    )
    inactive_with_photo = user_factory(
        email="inactive-photo@example.com",
        gender=Profile.Gender.FEMALE,
        interested_genders=[Profile.Gender.MALE],
    )
    active_without_photo = user_factory(
        email="active-no-photo@example.com",
        gender=Profile.Gender.FEMALE,
        interested_genders=[Profile.Gender.MALE],
    )
    male_profile = user_factory(
        email="active-male@example.com",
        gender=Profile.Gender.MALE,
        interested_genders=[Profile.Gender.FEMALE],
    )
    candidates = [
        active_with_photo,
        inactive_with_photo,
        active_without_photo,
        male_profile,
    ]
    for candidate in candidates:
        candidate.profile.visibility_status = Profile.Visibility.PUBLISHED
        candidate.profile.save(update_fields=["visibility_status"])
    active_with_photo.last_seen_at = timezone.now()
    active_without_photo.last_seen_at = timezone.now()
    male_profile.last_seen_at = timezone.now()
    inactive_with_photo.last_seen_at = timezone.now() - timezone.timedelta(days=30)
    for candidate in candidates:
        candidate.save(update_fields=["last_seen_at"])
    for candidate in [active_with_photo, inactive_with_photo, male_profile]:
        ProfilePhoto.objects.create(
            profile=candidate.profile,
            object_key=f"profiles/{candidate.pk}/photo.webp",
            public_url=f"https://example.test/{candidate.pk}.webp",
            thumbnail_object_key=f"profiles/{candidate.pk}/thumb.webp",
            thumbnail_url=f"https://example.test/{candidate.pk}-thumb.webp",
            position=0,
            is_primary=True,
            mime_type="image/webp",
            file_size=100,
            width=1200,
            height=1500,
        )

    api_client.force_authenticate(viewer)
    response = api_client.get(
        "/api/v1/discover",
        {
            "gender": Profile.Gender.FEMALE,
            "has_photo": "true",
            "active_within_days": "7",
        },
    )
    assert response.status_code == 200
    public_ids = {item["public_id"] for item in response.data["results"]}
    assert public_ids == {str(active_with_photo.profile.public_id)}


def test_read_receipt_is_persisted_and_visible_to_sender(api_client, user_factory):
    sender = user_factory(email="receipt-sender@example.com")
    reader = user_factory(email="receipt-reader@example.com")
    conversation = accepted_conversation(sender, reader)
    first = Message.objects.create(
        conversation=conversation,
        sender=sender,
        client_message_id="10000000-0000-0000-0000-000000000001",
        text="Tin nhắn thứ nhất",
    )
    second = Message.objects.create(
        conversation=conversation,
        sender=sender,
        client_message_id="10000000-0000-0000-0000-000000000002",
        text="Tin nhắn thứ hai",
    )

    api_client.force_authenticate(reader)
    response = api_client.post(
        f"/api/v1/conversations/{conversation.pk}/read",
        {"message_id": str(second.pk)},
        format="json",
    )
    assert response.status_code == 204
    membership = ConversationMember.objects.get(
        conversation=conversation, user=reader
    )
    assert membership.last_read_message_id == second.pk

    # An older marker must never regress the durable read state.
    response = api_client.post(
        f"/api/v1/conversations/{conversation.pk}/read",
        {"message_id": str(first.pk)},
        format="json",
    )
    assert response.status_code == 204
    membership.refresh_from_db()
    assert membership.last_read_message_id == second.pk

    api_client.force_authenticate(sender)
    response = api_client.get(f"/api/v1/conversations/{conversation.pk}")
    assert response.status_code == 200
    assert response.data["other_last_read_message_id"] == str(second.pk)
    assert response.data["other_last_read_at"] is not None


def test_profile_image_is_normalized_to_four_by_five(monkeypatch):
    source = Image.new("RGB", (2000, 1000), "white")
    buffer = BytesIO()
    source.save(buffer, "JPEG")
    stored = {}

    monkeypatch.setattr(
        image_processing,
        "get_object_bytes",
        lambda bucket, key: (buffer.getvalue(), {"ContentType": "image/jpeg"}),
    )
    monkeypatch.setattr(
        image_processing,
        "put_object_bytes",
        lambda bucket, key, data, content_type, public: stored.update({key: data}),
    )
    monkeypatch.setattr(image_processing, "delete_object", lambda bucket, key: None)

    result = image_processing.normalize_profile_image(
        "profile-media", "profiles/user/source.jpg"
    )
    assert result["width"] == 1200
    assert result["height"] == 1500
    normalized = Image.open(BytesIO(stored[result["object_key"]]))
    assert normalized.size == (1200, 1500)

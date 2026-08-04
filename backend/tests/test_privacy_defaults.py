import pytest
from django.utils import timezone

from apps.connections.models import ConnectionRequest
from apps.profiles.models import Profile


pytestmark = pytest.mark.django_db


def test_income_is_connection_only_by_default(api_client, user_factory):
    viewer = user_factory(email="privacy-viewer@example.com")
    target = user_factory(email="privacy-target@example.com")
    target.profile.visibility_status = Profile.Visibility.PUBLISHED
    target.profile.income_band = Profile.Income.FROM_20_30
    target.profile.field_visibility = {}
    target.profile.save(
        update_fields=["visibility_status", "income_band", "field_visibility"]
    )

    api_client.force_authenticate(viewer)
    response = api_client.get(f"/api/v1/profiles/{target.profile.public_id}")
    assert response.status_code == 200
    assert response.data["income_band"] is None

    ConnectionRequest.objects.create(
        sender=viewer,
        receiver=target,
        intro_message="Xin chào",
        status=ConnectionRequest.Status.ACCEPTED,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )
    response = api_client.get(f"/api/v1/profiles/{target.profile.public_id}")
    assert response.status_code == 200
    assert response.data["income_band"] == Profile.Income.FROM_20_30


def test_owner_receives_explicit_privacy_defaults(api_client, user_factory):
    user = user_factory(email="privacy-owner@example.com")
    user.profile.field_visibility = {}
    user.profile.save(update_fields=["field_visibility"])
    api_client.force_authenticate(user)

    response = api_client.get("/api/v1/me/profile")
    assert response.status_code == 200
    assert response.data["field_visibility"]["income_band"] == "connections"

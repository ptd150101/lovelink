import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.profiles.models import Interest, OccupationCategory, Profile, ProfilePhoto, Province


@pytest.fixture
def mock_reference_data(db):
    Province.objects.create(code="01", name="Hà Nội", sort_order=0)
    Province.objects.create(code="79", name="TP. Hồ Chí Minh", sort_order=1)
    OccupationCategory.objects.create(name="Công nghệ thông tin")
    OccupationCategory.objects.create(name="Kinh doanh")
    for name in ("Du lịch", "Đọc sách", "Âm nhạc", "Công nghệ"):
        Interest.objects.create(name=name)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_mock_users_is_deterministic_and_idempotent(mock_reference_data):
    call_command(
        "seed_mock_users",
        count=12,
        batch_size=5,
        with_interests=True,
        with_photos=True,
    )

    user_model = get_user_model()
    assert user_model.objects.filter(email__startswith="mock.").count() == 12
    assert Profile.objects.filter(user__email__startswith="mock.").count() == 12
    assert ProfilePhoto.objects.filter(profile__user__email__startswith="mock.").count() == 12
    assert Profile.interests.through.objects.filter(
        profile__user__email__startswith="mock."
    ).count() == 36

    first = user_model.objects.get(email="mock.000000001@lovelink.local")
    assert first.check_password("MockPassword123!")
    assert first.profile.visibility_status == Profile.Visibility.PUBLISHED

    first_user_id = first.id
    first_public_id = first.profile.public_id

    call_command(
        "seed_mock_users",
        count=12,
        batch_size=4,
        with_interests=True,
        with_photos=True,
    )

    first.refresh_from_db()
    first.profile.refresh_from_db()
    assert user_model.objects.filter(email__startswith="mock.").count() == 12
    assert Profile.objects.filter(user__email__startswith="mock.").count() == 12
    assert ProfilePhoto.objects.filter(profile__user__email__startswith="mock.").count() == 12
    assert Profile.interests.through.objects.filter(
        profile__user__email__startswith="mock."
    ).count() == 36
    assert first.id == first_user_id
    assert first.profile.public_id == first_public_id


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_seed_mock_users_refuses_non_debug_environment(mock_reference_data):
    with pytest.raises(CommandError, match="DEBUG/local"):
        call_command("seed_mock_users", count=1)

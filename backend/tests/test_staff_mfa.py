import pytest
from django.test import override_settings
from django.utils import timezone

from apps.accounts.mfa import encrypt_secret, totp_code
from apps.accounts.models import StaffTotpDevice


pytestmark = pytest.mark.django_db


@override_settings(STAFF_MFA_REQUIRED=True)
def test_staff_admin_login_requires_valid_totp(client, user_factory):
    staff = user_factory(email="mfa-admin@example.com")
    staff.is_staff = True
    staff.is_superuser = True
    staff.save(update_fields=["is_staff", "is_superuser"])
    secret = "JBSWY3DPEHPK3PXP"
    StaffTotpDevice.objects.create(
        user=staff,
        encrypted_secret=encrypt_secret(secret),
        is_active=True,
        confirmed_at=timezone.now(),
    )

    missing = client.post(
        "/admin/login/?next=/admin/",
        {
            "username": staff.email,
            "password": "StrongPassword123!",
            "otp_code": "",
            "next": "/admin/",
        },
    )
    assert missing.status_code == 200
    assert "Mã xác thực" in missing.content.decode("utf-8")

    valid = client.post(
        "/admin/login/?next=/admin/",
        {
            "username": staff.email,
            "password": "StrongPassword123!",
            "otp_code": totp_code(secret),
            "next": "/admin/",
        },
    )
    assert valid.status_code == 302
    assert valid.url == "/admin/"

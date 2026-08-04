import pytest
from django.core.cache import cache
from django.test import override_settings


pytestmark = pytest.mark.django_db


@override_settings(
    LOGIN_IDENTITY_FAILURE_LIMIT=3,
    LOGIN_IDENTITY_IP_FAILURE_LIMIT=3,
    LOGIN_FAILURE_WINDOW_SECONDS=300,
    LOGIN_LOCKOUT_SECONDS=300,
)
def test_login_is_temporarily_locked_after_repeated_failures(api_client, user_factory):
    user_factory(email="locked@example.com")
    cache.clear()

    for _ in range(3):
        response = api_client.post(
            "/api/v1/auth/login",
            {
                "email": "locked@example.com",
                "password": "WrongPassword123!",
            },
            format="json",
            REMOTE_ADDR="203.0.113.8",
        )
        assert response.status_code == 400

    # A correct password remains blocked during the temporary lock window.
    response = api_client.post(
        "/api/v1/auth/login",
        {
            "email": "locked@example.com",
            "password": "StrongPassword123!",
        },
        format="json",
        REMOTE_ADDR="203.0.113.8",
    )
    assert response.status_code == 400
    assert "Email hoặc mật khẩu" in str(response.data)

    cache.clear()
    response = api_client.post(
        "/api/v1/auth/login",
        {
            "email": "locked@example.com",
            "password": "StrongPassword123!",
        },
        format="json",
        REMOTE_ADDR="203.0.113.8",
    )
    assert response.status_code == 200

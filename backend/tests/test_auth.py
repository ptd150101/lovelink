import pytest
from django.core import mail
from apps.accounts.models import User
from apps.profiles.models import Profile

@pytest.mark.django_db
def test_registration_creates_pending_account_profile_and_email(api_client):
 response=api_client.post("/api/v1/auth/register",{"email":"new@example.com","password":"VeryStrongPassword123!","password_confirm":"VeryStrongPassword123!","birth_date":"2000-01-01","accept_terms":True},format="json")
 assert response.status_code==201
 user=User.objects.get(email="new@example.com")
 assert user.status==User.Status.PENDING and Profile.objects.filter(user=user).exists()
 assert len(mail.outbox)==1

@pytest.mark.django_db
def test_login_uses_generic_error(api_client):
 response=api_client.post("/api/v1/auth/login",{"email":"missing@example.com","password":"wrong"},format="json")
 assert response.status_code==400
 assert "Email hoặc mật khẩu" in str(response.data)

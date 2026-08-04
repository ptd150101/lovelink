from django.conf import settings
from django.core.mail import send_mail
from .tokens import email_token, password_token

def send_verification_email(user):
    token = email_token(user)
    url = f"{settings.APP_URL}/auth/verify-email?token={token}"
    send_mail("Xác minh tài khoản LoveLink", f"Mở liên kết để xác minh tài khoản: {url}", settings.DEFAULT_FROM_EMAIL, [user.email])

def send_password_reset_email(user):
    token = password_token(user)
    url = f"{settings.APP_URL}/auth/reset-password?token={token}"
    send_mail("Đặt lại mật khẩu LoveLink", f"Mở liên kết để đặt lại mật khẩu: {url}", settings.DEFAULT_FROM_EMAIL, [user.email])

from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError

from .mfa import staff_mfa_required, verify_device_code


class StaffMfaAuthenticationForm(AdminAuthenticationForm):
    otp_code = forms.CharField(
        label="Mã xác thực 6 chữ số",
        required=False,
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
                "autofocus": False,
            }
        ),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        device = getattr(user, "staff_totp_device", None)
        required = staff_mfa_required() or bool(device and device.is_active)
        if not required:
            return
        if not device or not device.is_active or not device.confirmed_at:
            raise ValidationError(
                "Tài khoản nhân viên chưa được đăng ký MFA. Hãy liên hệ quản trị viên.",
                code="staff_mfa_not_enrolled",
            )
        code = str(self.cleaned_data.get("otp_code", "")).strip()
        if not verify_device_code(device, code):
            raise ValidationError(
                "Mã xác thực không đúng, đã hết hạn hoặc đã được sử dụng.",
                code="invalid_staff_mfa",
            )

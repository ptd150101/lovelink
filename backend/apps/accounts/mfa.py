import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import transaction

from .models import StaffTotpDevice


def _fernet() -> Fernet:
    key = hashlib.sha256(f"{settings.SECRET_KEY}:staff-mfa".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(encrypted_secret: str) -> str:
    return _fernet().decrypt(encrypted_secret.encode()).decode()


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _secret_bytes(secret: str) -> bytes:
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode(padded, casefold=True)


def totp_code(secret: str, at_time: float | None = None, step_seconds: int = 30) -> str:
    counter = int((time.time() if at_time is None else at_time) // step_seconds)
    digest = hmac.new(
        _secret_bytes(secret), struct.pack(">Q", counter), hashlib.sha1
    ).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def verify_device_code(device: StaffTotpDevice, code: str, at_time: float | None = None) -> bool:
    if not device.is_active or not device.confirmed_at or not code.isdigit() or len(code) != 6:
        return False
    current_time = time.time() if at_time is None else at_time
    current_step = int(current_time // 30)
    secret = decrypt_secret(device.encrypted_secret)
    with transaction.atomic():
        locked = StaffTotpDevice.objects.select_for_update().get(pk=device.pk)
        for offset in (-1, 0, 1):
            step = current_step + offset
            if step <= locked.last_used_step:
                continue
            expected = totp_code(secret, at_time=step * 30)
            if hmac.compare_digest(expected, code):
                locked.last_used_step = step
                locked.save(update_fields=["last_used_step", "updated_at"])
                device.last_used_step = step
                return True
    return False


def provisioning_uri(user_email: str, secret: str) -> str:
    issuer = os.getenv("STAFF_MFA_ISSUER", "LoveLink")
    label = quote(f"{issuer}:{user_email}")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}"
        "&algorithm=SHA1&digits=6&period=30"
    )


def staff_mfa_required() -> bool:
    value = os.getenv(
        "STAFF_MFA_REQUIRED",
        str(getattr(settings, "STAFF_MFA_REQUIRED", False)),
    )
    return value.lower() in {"1", "true", "yes", "on"}

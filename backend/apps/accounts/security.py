import hashlib

from django.conf import settings
from django.core.cache import cache


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _keys(email: str, ip_address: str):
    normalized = email.lower().strip()
    identity = _digest(normalized)
    identity_ip = _digest(f"{normalized}|{ip_address or '-'}")
    return {
        "identity_failures": f"auth:login:failures:identity:{identity}",
        "identity_lock": f"auth:login:lock:identity:{identity}",
        "identity_ip_failures": f"auth:login:failures:identity-ip:{identity_ip}",
        "identity_ip_lock": f"auth:login:lock:identity-ip:{identity_ip}",
    }


def login_is_locked(email: str, ip_address: str) -> bool:
    keys = _keys(email, ip_address)
    return bool(cache.get(keys["identity_lock"]) or cache.get(keys["identity_ip_lock"]))


def record_login_failure(email: str, ip_address: str) -> bool:
    keys = _keys(email, ip_address)
    window = getattr(settings, "LOGIN_FAILURE_WINDOW_SECONDS", 900)
    lock_seconds = getattr(settings, "LOGIN_LOCKOUT_SECONDS", 900)
    identity_limit = getattr(settings, "LOGIN_IDENTITY_FAILURE_LIMIT", 8)
    identity_ip_limit = getattr(settings, "LOGIN_IDENTITY_IP_FAILURE_LIMIT", 5)
    locked = False

    for failure_key, lock_key, limit in [
        (keys["identity_failures"], keys["identity_lock"], identity_limit),
        (
            keys["identity_ip_failures"],
            keys["identity_ip_lock"],
            identity_ip_limit,
        ),
    ]:
        failures = int(cache.get(failure_key, 0)) + 1
        cache.set(failure_key, failures, timeout=window)
        if failures >= limit:
            cache.set(lock_key, True, timeout=lock_seconds)
            locked = True
    return locked


def clear_login_failures(email: str, ip_address: str) -> None:
    cache.delete_many(list(_keys(email, ip_address).values()))

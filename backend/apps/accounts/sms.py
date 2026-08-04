from __future__ import annotations

import base64
import logging
from urllib import parse, request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class SmsDeliveryError(RuntimeError):
    pass


def _console_send(phone: str, body: str) -> None:
    logger.warning("LoveLink SMS to %s: %s", phone, body)


def _twilio_send(phone: str, body: str) -> None:
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    sender = settings.TWILIO_FROM_NUMBER
    messaging_service_sid = settings.TWILIO_MESSAGING_SERVICE_SID
    if not account_sid or not auth_token or not (sender or messaging_service_sid):
        raise ImproperlyConfigured(
            "Twilio requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and either "
            "TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID."
        )

    payload = {"To": phone, "Body": body}
    if messaging_service_sid:
        payload["MessagingServiceSid"] = messaging_service_sid
    else:
        payload["From"] = sender

    endpoint = (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{parse.quote(account_sid)}/Messages.json"
    )
    encoded = parse.urlencode(payload).encode("utf-8")
    token = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    sms_request = request.Request(
        endpoint,
        data=encoded,
        method="POST",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with request.urlopen(sms_request, timeout=10) as response:
            if response.status < 200 or response.status >= 300:
                raise SmsDeliveryError(f"Twilio returned HTTP {response.status}")
    except Exception as exc:
        if isinstance(exc, SmsDeliveryError):
            raise
        raise SmsDeliveryError("Không thể gửi SMS qua Twilio.") from exc


def send_sms(phone: str, body: str) -> None:
    backend = settings.SMS_BACKEND.lower().strip()
    if backend == "console":
        _console_send(phone, body)
        return
    if backend == "twilio":
        _twilio_send(phone, body)
        return
    raise ImproperlyConfigured(f"SMS_BACKEND không được hỗ trợ: {backend}")

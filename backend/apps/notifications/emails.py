from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from .models import Notification


PREFERENCE_BY_TYPE = {
    Notification.Type.CONNECTION_RECEIVED: "email_connection_notifications",
    Notification.Type.CONNECTION_ACCEPTED: "email_connection_notifications",
    Notification.Type.MESSAGE_RECEIVED: "email_message_notifications",
    Notification.Type.VERIFICATION_NEEDS_MORE: "email_verification_notifications",
    Notification.Type.VERIFICATION_APPROVED: "email_verification_notifications",
    Notification.Type.VERIFICATION_REJECTED: "email_verification_notifications",
    Notification.Type.ACCOUNT_WARNING: None,
}


def email_allowed(notification: Notification) -> bool:
    if notification.type not in PREFERENCE_BY_TYPE:
        return False
    preference_name = PREFERENCE_BY_TYPE[notification.type]
    if preference_name is None:
        return True
    preferences = getattr(notification.user, "preferences", None)
    if preferences is None:
        from apps.accounts.models import UserPreference

        preferences, _ = UserPreference.objects.get_or_create(user=notification.user)
    return bool(getattr(preferences, preference_name))


def notification_url(notification: Notification) -> str:
    base = settings.APP_URL.rstrip("/")
    if notification.type in {
        Notification.Type.CONNECTION_RECEIVED,
        Notification.Type.CONNECTION_ACCEPTED,
        Notification.Type.CONNECTION_DECLINED,
    }:
        return f"{base}/connections"
    if notification.type == Notification.Type.MESSAGE_RECEIVED:
        return f"{base}/messages/{notification.entity_id}"
    if notification.type.startswith("verification."):
        return f"{base}/verification"
    return f"{base}/notifications"


def render_notification_email(notification: Notification) -> tuple[str, str]:
    subject = f"LoveLink — {notification.title}"
    body = (
        f"{notification.title}\n\n"
        f"{notification.body}\n\n"
        f"Mở LoveLink: {notification_url(notification)}\n\n"
        "Bạn có thể thay đổi tùy chọn email trong phần Cài đặt thông báo."
    )
    return subject, body


def schedule_notification_email(notification: Notification) -> None:
    if not email_allowed(notification):
        return

    countdown = 0
    if notification.type == Notification.Type.MESSAGE_RECEIVED:
        dedupe_key = (
            f"notification-email:message:{notification.user_id}:"
            f"{notification.entity_id}"
        )
        delay = int(getattr(settings, "EMAIL_MESSAGE_NOTIFICATION_DELAY", 300))
        if not cache.add(dedupe_key, str(notification.pk), timeout=delay):
            return
        countdown = delay

    from .tasks import send_notification_email

    transaction.on_commit(
        lambda: send_notification_email.apply_async(
            args=[str(notification.pk)], countdown=countdown
        )
    )

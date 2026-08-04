from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .emails import email_allowed, render_notification_email
from .models import Notification


@shared_task(ignore_result=True)
def send_notification_email(notification_id: str):
    notification = (
        Notification.objects.select_related("user", "user__preferences")
        .filter(pk=notification_id)
        .first()
    )
    if not notification or not notification.user.email or not email_allowed(notification):
        return False
    subject, body = render_notification_email(notification)
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [notification.user.email],
        fail_silently=False,
    )
    return True

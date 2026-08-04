from celery import shared_task
from django.utils import timezone
from .models import ConnectionRequest
@shared_task
def expire_connection_requests():
 return ConnectionRequest.objects.filter(status=ConnectionRequest.Status.PENDING,expires_at__lte=timezone.now()).update(status=ConnectionRequest.Status.EXPIRED,responded_at=timezone.now())

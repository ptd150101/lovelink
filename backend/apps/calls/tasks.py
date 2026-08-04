from celery import shared_task
from django.utils import timezone
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from .models import CallSession
@shared_task
def expire_ringing_calls():
 cutoff=timezone.now()-timezone.timedelta(seconds=30)
 for call in CallSession.objects.filter(status=CallSession.Status.RINGING,ringing_at__lte=cutoff).select_related("caller","callee"):
  call.status=CallSession.Status.MISSED;call.ended_at=timezone.now();call.end_reason="timeout";call.save(update_fields=["status","ended_at","end_reason"])
  push_notification(user=call.callee,type=Notification.Type.CALL_MISSED,title="Cuộc gọi nhỡ",body=f"{call.caller.profile.display_name} đã gọi cho bạn.",actor=call.caller,entity=call)

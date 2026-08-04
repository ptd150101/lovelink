from celery import shared_task
from django.utils import timezone
from .models import User

@shared_task
def finalize_account_deletions():
    for user in User.objects.filter(status=User.Status.SCHEDULED_DELETION, scheduled_deletion_at__lte=timezone.now()).iterator():
        user.email=f"deleted-{user.pk}@invalid.local"; user.phone=None; user.is_active=False; user.status=User.Status.DELETED; user.set_unusable_password(); user.save()
        if hasattr(user,"profile"):
            p=user.profile; p.display_name="Người dùng đã xóa"; p.bio=""; p.looking_for=""; p.visibility_status="deleted"; p.save()

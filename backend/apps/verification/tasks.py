from celery import shared_task
from django.conf import settings
from django.utils import timezone
from common.storage.s3 import delete_object
from .models import VerificationEvidence,VerificationRequest
@shared_task
def purge_expired_evidence():
 cutoff=timezone.now()-timezone.timedelta(days=settings.VERIFICATION_EVIDENCE_RETENTION_DAYS)
 qs=VerificationEvidence.objects.filter(deleted_at__isnull=True,request__decided_at__lte=cutoff,request__status__in=[VerificationRequest.Status.VERIFIED,VerificationRequest.Status.REJECTED,VerificationRequest.Status.REVOKED])
 for e in qs.iterator():
  try:delete_object(settings.S3_VERIFICATION_BUCKET,e.private_object_key)
  except Exception:continue
  e.deleted_at=timezone.now();e.save(update_fields=["deleted_at"])

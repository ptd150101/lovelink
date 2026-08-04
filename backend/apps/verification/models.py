import uuid
from django.conf import settings
from django.db import models
class VerificationRequest(models.Model):
 class Status(models.TextChoices):DRAFT="draft","Bản nháp";SUBMITTED="submitted","Đã gửi";IN_REVIEW="in_review","Đang xét duyệt";NEEDS_MORE="needs_more_info","Cần bổ sung";VERIFIED="verified","Đã xác minh";REJECTED="rejected","Từ chối";EXPIRED="expired","Hết hạn";REVOKED="revoked","Thu hồi"
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="verification_requests")
 status=models.CharField(max_length=24,choices=Status.choices,default=Status.DRAFT,db_index=True)
 challenge_code=models.CharField(max_length=12)
 submitted_at=models.DateTimeField(null=True,blank=True,db_index=True)
 review_started_at=models.DateTimeField(null=True,blank=True)
 decided_at=models.DateTimeField(null=True,blank=True)
 assigned_reviewer=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="assigned_verifications")
 decision_reason_code=models.CharField(max_length=64,blank=True)
 user_visible_reason=models.TextField(blank=True)
 internal_note=models.TextField(blank=True)
 expires_at=models.DateTimeField(null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta:permissions=[("review_verificationrequest","Can review verification requests")];indexes=[models.Index(fields=["status","submitted_at"])]

class VerificationEvidence(models.Model):
 class Type(models.TextChoices):ID_FRONT="id_front","Mặt trước giấy tờ";SELFIE="selfie","Ảnh selfie";CHALLENGE="challenge_selfie","Selfie với mã"
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 request=models.ForeignKey(VerificationRequest,on_delete=models.CASCADE,related_name="evidence")
 evidence_type=models.CharField(max_length=24,choices=Type.choices)
 private_object_key=models.CharField(max_length=500,unique=True)
 mime_type=models.CharField(max_length=100)
 file_size=models.PositiveBigIntegerField(default=0)
 uploaded_at=models.DateTimeField(auto_now_add=True)
 deleted_at=models.DateTimeField(null=True,blank=True)
 class Meta:constraints=[models.UniqueConstraint(fields=["request","evidence_type"],name="unique_evidence_type_per_request")]

class VerificationReview(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 request=models.ForeignKey(VerificationRequest,on_delete=models.CASCADE,related_name="reviews")
 reviewer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="verification_reviews")
 action=models.CharField(max_length=32)
 previous_status=models.CharField(max_length=24)
 new_status=models.CharField(max_length=24)
 reason_code=models.CharField(max_length=64,blank=True)
 internal_note=models.TextField(blank=True)
 created_at=models.DateTimeField(auto_now_add=True)

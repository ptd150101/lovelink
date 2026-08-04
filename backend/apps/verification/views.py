import secrets,uuid
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.permissions import IsReviewer
from common.storage.s3 import head_object,presign_get,presign_put
from apps.audit.services import audit
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from apps.profiles.models import Profile
from .models import VerificationRequest,VerificationEvidence,VerificationReview
from .serializers import VerificationRequestSerializer,StaffVerificationSerializer
ALLOWED={"image/jpeg":"jpg","image/png":"png","image/webp":"webp"}

class VerificationCurrentView(APIView):
 def get(self,request):
  obj=VerificationRequest.objects.filter(user=request.user).order_by("-created_at").first();return Response(VerificationRequestSerializer(obj).data if obj else None)

class VerificationCreateView(APIView):
 def post(self,request):
  active=VerificationRequest.objects.filter(user=request.user,status__in=[VerificationRequest.Status.DRAFT,VerificationRequest.Status.SUBMITTED,VerificationRequest.Status.IN_REVIEW,VerificationRequest.Status.NEEDS_MORE]).first()
  if active:return Response(VerificationRequestSerializer(active).data)
  obj=VerificationRequest.objects.create(user=request.user,challenge_code=secrets.token_hex(3).upper(),expires_at=timezone.now()+timezone.timedelta(days=7));return Response(VerificationRequestSerializer(obj).data,status=201)

class EvidencePresignView(APIView):
 def post(self,request):
  vr=get_object_or_404(VerificationRequest,pk=request.data.get("request_id"),user=request.user,status__in=[VerificationRequest.Status.DRAFT,VerificationRequest.Status.NEEDS_MORE])
  typ=request.data.get("evidence_type");ct=request.data.get("content_type");size=int(request.data.get("size",0))
  if typ not in VerificationEvidence.Type.values or ct not in ALLOWED or size<=0 or size>10*1024*1024:return Response({"detail":"File xác minh không hợp lệ."},status=400)
  key=f"verification/{request.user.pk}/{vr.pk}/{typ}-{uuid.uuid4().hex}.{ALLOWED[ct]}";signed=presign_put(settings.S3_VERIFICATION_BUCKET,key,ct)
  return Response({"object_key":key,"upload_url":signed.upload_url,"headers":signed.headers,"expires_in":600})

class EvidenceCompleteView(APIView):
 def post(self,request):
  vr=get_object_or_404(VerificationRequest,pk=request.data.get("request_id"),user=request.user,status__in=[VerificationRequest.Status.DRAFT,VerificationRequest.Status.NEEDS_MORE]);key=request.data.get("object_key","");typ=request.data.get("evidence_type")
  if not key.startswith(f"verification/{request.user.pk}/{vr.pk}/") or typ not in VerificationEvidence.Type.values:return Response({"detail":"Dữ liệu không hợp lệ."},status=400)
  try:meta=head_object(settings.S3_VERIFICATION_BUCKET,key)
  except Exception:return Response({"detail":"Không tìm thấy file."},status=400)
  obj,_=VerificationEvidence.objects.update_or_create(request=vr,evidence_type=typ,defaults={"private_object_key":key,"mime_type":meta.get("ContentType",""),"file_size":meta.get("ContentLength",0),"deleted_at":None});return Response({"id":obj.id,"evidence_type":obj.evidence_type},status=201)

class VerificationSubmitView(APIView):
 def post(self,request,pk):
  vr=get_object_or_404(VerificationRequest,pk=pk,user=request.user,status__in=[VerificationRequest.Status.DRAFT,VerificationRequest.Status.NEEDS_MORE]);needed=set(VerificationEvidence.Type.values);have=set(vr.evidence.filter(deleted_at__isnull=True).values_list("evidence_type",flat=True))
  if needed-have:return Response({"detail":"Cần đủ giấy tờ, selfie và selfie với mã thử thách.","missing":list(needed-have)},status=400)
  vr.status=VerificationRequest.Status.SUBMITTED;vr.submitted_at=timezone.now();vr.user_visible_reason="";vr.save(update_fields=["status","submitted_at","user_visible_reason","updated_at"]);audit(actor=request.user,action="verification.submitted",target=vr);return Response(VerificationRequestSerializer(vr).data)

class StaffVerificationListView(generics.ListAPIView):
 permission_classes=[IsReviewer];serializer_class=StaffVerificationSerializer
 def get_queryset(self):return VerificationRequest.objects.filter(status__in=[VerificationRequest.Status.SUBMITTED,VerificationRequest.Status.IN_REVIEW]).select_related("user__profile").prefetch_related("user__profile__photos","evidence").order_by("submitted_at")

class StaffVerificationDetailView(APIView):
 permission_classes=[IsReviewer]
 def get(self,request,pk):
  vr=get_object_or_404(VerificationRequest.objects.select_related("user__profile").prefetch_related("evidence","user__profile__photos"),pk=pk)
  data=StaffVerificationSerializer(vr).data;data["evidence_urls"]=[{"type":e.evidence_type,"url":presign_get(settings.S3_VERIFICATION_BUCKET,e.private_object_key,300)} for e in vr.evidence.filter(deleted_at__isnull=True)];return Response(data)

class StaffVerificationActionView(APIView):
 permission_classes=[IsReviewer]
 def post(self,request,pk):
  action=request.data.get("action");allowed={"start":VerificationRequest.Status.IN_REVIEW,"request_more":VerificationRequest.Status.NEEDS_MORE,"approve":VerificationRequest.Status.VERIFIED,"reject":VerificationRequest.Status.REJECTED,"revoke":VerificationRequest.Status.REVOKED}
  if action not in allowed:return Response({"detail":"Hành động không hợp lệ."},status=400)
  with transaction.atomic():
   vr=get_object_or_404(VerificationRequest.objects.select_for_update().select_related("user__profile"),pk=pk);before=vr.status;new=allowed[action];reason=str(request.data.get("reason_code",""));visible=str(request.data.get("user_visible_reason",""));note=str(request.data.get("internal_note",""))
   vr.status=new;vr.assigned_reviewer=request.user;vr.internal_note=note;vr.decision_reason_code=reason;vr.user_visible_reason=visible
   if action=="start":vr.review_started_at=timezone.now()
   if action in {"approve","reject","revoke"}:vr.decided_at=timezone.now()
   vr.save()
   VerificationReview.objects.create(request=vr,reviewer=request.user,action=action,previous_status=before,new_status=new,reason_code=reason,internal_note=note)
   profile=vr.user.profile
   if action=="approve":profile.verification_level=Profile.VerificationLevel.IDENTITY;profile.verified_at=timezone.now();profile.save(update_fields=["verification_level","verified_at","updated_at"]);nt=Notification.Type.VERIFICATION_APPROVED;title="Xác minh danh tính thành công"
   elif action=="request_more":nt=Notification.Type.VERIFICATION_NEEDS_MORE;title="Cần bổ sung hồ sơ xác minh"
   elif action=="reject":nt=Notification.Type.VERIFICATION_REJECTED;title="Hồ sơ xác minh chưa được chấp nhận"
   elif action=="revoke":profile.verification_level=Profile.VerificationLevel.REVOKED;profile.save(update_fields=["verification_level","updated_at"]);nt=Notification.Type.ACCOUNT_WARNING;title="Tích xanh đã được thu hồi"
   else:nt=None;title=""
  if nt:push_notification(user=vr.user,type=nt,title=title,body=visible,entity=vr)
  audit(actor=request.user,action=f"verification.{action}",target=vr,before={"status":before},after={"status":new,"reason":reason})
  return Response(StaffVerificationSerializer(vr).data)

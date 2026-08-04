from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.permissions import IsModerator
from apps.accounts.models import User
from apps.audit.services import audit
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from apps.profiles.models import Profile,ProfilePhoto
from .models import Block,Report,ModerationAction
from .serializers import BlockSerializer,ReportSerializer

class BlockListView(generics.ListAPIView):
 serializer_class=BlockSerializer
 def get_queryset(self):return Block.objects.filter(blocker=self.request.user).select_related("blocked__profile")

class BlockView(APIView):
 def post(self,request,public_id):
  target=get_object_or_404(User,profile__public_id=public_id)
  if target==request.user:return Response({"detail":"Không thể tự chặn."},status=400)
  with transaction.atomic():
   block,_=Block.objects.get_or_create(blocker=request.user,blocked=target)
   from apps.connections.models import ConnectionRequest
   ConnectionRequest.objects.filter(sender__in=[request.user,target],receiver__in=[request.user,target],status=ConnectionRequest.Status.PENDING).update(status=ConnectionRequest.Status.BLOCKED,responded_at=timezone.now())
   from apps.calls.models import CallSession
   active=CallSession.objects.filter(caller__in=[request.user,target],callee__in=[request.user,target],status__in=CallSession.ACTIVE_STATES)
   active.update(status=CallSession.Status.ENDED,ended_at=timezone.now(),end_reason="blocked")
  audit(actor=request.user,action="user.blocked",target=target)
  return Response(BlockSerializer(block).data,status=201)
 def delete(self,request,public_id):
  Block.objects.filter(blocker=request.user,blocked__profile__public_id=public_id).delete();return Response(status=204)

class ReportCreateView(APIView):
 def post(self,request):
  target=get_object_or_404(User,profile__public_id=request.data.get("reported_user_public_id"))
  target_type=request.data.get("target_type");target_id=str(request.data.get("target_id",target.profile.public_id));reason=request.data.get("reason_code")
  if target_type not in Report.Target.values or reason not in Report.Reason.values:return Response({"detail":"Dữ liệu báo cáo không hợp lệ."},status=400)
  recent=Report.objects.filter(reporter=request.user,reported_user=target,target_type=target_type,target_id=target_id,created_at__gte=timezone.now()-timezone.timedelta(hours=24)).exists()
  if recent:return Response({"detail":"Bạn đã báo cáo nội dung này."},status=409)
  report=Report.objects.create(reporter=request.user,reported_user=target,target_type=target_type,target_id=target_id,reason_code=reason,description=str(request.data.get("description",""))[:2000])
  audit(actor=request.user,action="report.created",target=report);return Response(ReportSerializer(report).data,status=201)

class StaffReportListView(generics.ListAPIView):
 permission_classes=[IsModerator];serializer_class=ReportSerializer
 def get_queryset(self):return Report.objects.select_related("reported_user","reporter").filter(status__in=[Report.Status.OPEN,Report.Status.IN_REVIEW]).order_by("created_at")

class StaffReportActionView(APIView):
 permission_classes=[IsModerator]
 def post(self,request,pk):
  report=get_object_or_404(Report,pk=pk);action=request.data.get("action");reason=str(request.data.get("reason","")).strip()
  if action not in ModerationAction.Action.values or not reason:return Response({"detail":"Hành động hoặc lý do không hợp lệ."},status=400)
  target=report.reported_user
  with transaction.atomic():
   mod=ModerationAction.objects.create(moderator=request.user,target_user=target,report=report,action=action,reason=reason,expires_at=request.data.get("expires_at") or None)
   if action==ModerationAction.Action.WARN:push_notification(user=target,type=Notification.Type.ACCOUNT_WARNING,title="Cảnh báo tài khoản",body=reason)
   elif action==ModerationAction.Action.HIDE_PROFILE:target.profile.visibility_status=Profile.Visibility.HIDDEN_MOD;target.profile.save(update_fields=["visibility_status","updated_at"])
   elif action==ModerationAction.Action.HIDE_PHOTO:ProfilePhoto.objects.filter(pk=report.target_id,profile__user=target).update(moderation_status=ProfilePhoto.Moderation.REJECTED)
   elif action==ModerationAction.Action.SUSPEND:target.status=User.Status.SUSPENDED;target.save(update_fields=["status","updated_at"]);target.profile.visibility_status=Profile.Visibility.SUSPENDED;target.profile.save(update_fields=["visibility_status","updated_at"])
   elif action==ModerationAction.Action.BAN:target.status=User.Status.BANNED;target.is_active=False;target.save(update_fields=["status","is_active","updated_at"]);target.profile.visibility_status=Profile.Visibility.SUSPENDED;target.profile.save(update_fields=["visibility_status","updated_at"])
   elif action==ModerationAction.Action.REVOKE_BADGE:target.profile.verification_level=Profile.VerificationLevel.REVOKED;target.profile.save(update_fields=["verification_level","updated_at"])
   elif action==ModerationAction.Action.RESTORE:target.status=User.Status.ACTIVE;target.is_active=True;target.save(update_fields=["status","is_active","updated_at"]);target.profile.visibility_status=Profile.Visibility.PUBLISHED;target.profile.save(update_fields=["visibility_status","updated_at"])
   report.status=Report.Status.ACTION;report.resolution=reason;report.assigned_moderator=request.user;report.resolved_at=timezone.now();report.save(update_fields=["status","resolution","assigned_moderator","resolved_at"])
  audit(actor=request.user,action=f"moderation.{action}",target=target,after={"reason":reason,"report":str(report.pk)})
  return Response(ReportSerializer(report).data)

class StaffReportDismissView(APIView):
 permission_classes=[IsModerator]
 def post(self,request,pk):
  r=get_object_or_404(Report,pk=pk);r.status=Report.Status.DISMISSED;r.resolution=str(request.data.get("reason","Không phát hiện vi phạm"));r.assigned_moderator=request.user;r.resolved_at=timezone.now();r.save();audit(actor=request.user,action="report.dismissed",target=r);return Response(ReportSerializer(r).data)

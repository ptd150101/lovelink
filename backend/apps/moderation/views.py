from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.audit.services import audit
from apps.calls.models import CallSession
from apps.connections.models import ConnectionRequest
from common.permissions import IsModerator

from .models import Block, Report
from .serializers import BlockSerializer, ReportSerializer
from .services import (
    ModerationServiceError,
    apply_moderation_action,
    dismiss_report,
)


class BlockListView(generics.ListAPIView):
    serializer_class = BlockSerializer

    def get_queryset(self):
        return Block.objects.filter(blocker=self.request.user).select_related(
            "blocked__profile"
        )


class BlockView(APIView):
    def post(self, request, public_id):
        target = get_object_or_404(User, profile__public_id=public_id)
        if target == request.user:
            return Response({"detail": "Không thể tự chặn."}, status=400)
        with transaction.atomic():
            block, _ = Block.objects.get_or_create(
                blocker=request.user, blocked=target
            )
            ConnectionRequest.objects.filter(
                sender__in=[request.user, target],
                receiver__in=[request.user, target],
                status=ConnectionRequest.Status.PENDING,
            ).update(
                status=ConnectionRequest.Status.BLOCKED,
                responded_at=timezone.now(),
            )
            CallSession.objects.filter(
                caller__in=[request.user, target],
                callee__in=[request.user, target],
                status__in=CallSession.ACTIVE_STATES,
            ).update(
                status=CallSession.Status.ENDED,
                ended_at=timezone.now(),
                end_reason="blocked",
            )
        audit(actor=request.user, action="user.blocked", target=target)
        return Response(BlockSerializer(block).data, status=201)

    def delete(self, request, public_id):
        Block.objects.filter(
            blocker=request.user, blocked__profile__public_id=public_id
        ).delete()
        return Response(status=204)


class ReportCreateView(APIView):
    def post(self, request):
        target = get_object_or_404(
            User, profile__public_id=request.data.get("reported_user_public_id")
        )
        target_type = request.data.get("target_type")
        target_id = str(request.data.get("target_id", target.profile.public_id))
        reason = request.data.get("reason_code")
        if target_type not in Report.Target.values or reason not in Report.Reason.values:
            return Response({"detail": "Dữ liệu báo cáo không hợp lệ."}, status=400)
        recent = Report.objects.filter(
            reporter=request.user,
            reported_user=target,
            target_type=target_type,
            target_id=target_id,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24),
        ).exists()
        if recent:
            return Response(
                {"detail": "Bạn đã báo cáo nội dung này."}, status=409
            )
        report = Report.objects.create(
            reporter=request.user,
            reported_user=target,
            target_type=target_type,
            target_id=target_id,
            reason_code=reason,
            description=str(request.data.get("description", ""))[:2000],
        )
        audit(actor=request.user, action="report.created", target=report)
        return Response(ReportSerializer(report).data, status=201)


class StaffReportListView(generics.ListAPIView):
    permission_classes = [IsModerator]
    serializer_class = ReportSerializer

    def get_queryset(self):
        return (
            Report.objects.select_related("reported_user", "reporter")
            .filter(status__in=[Report.Status.OPEN, Report.Status.IN_REVIEW])
            .order_by("created_at")
        )


class StaffReportActionView(APIView):
    permission_classes = [IsModerator]

    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        expires_at = None
        if request.data.get("expires_at"):
            expires_at = parse_datetime(str(request.data["expires_at"]))
            if expires_at is None:
                return Response({"detail": "Thời hạn không hợp lệ."}, status=400)
        try:
            report = apply_moderation_action(
                report=report,
                moderator=request.user,
                action=str(request.data.get("action", "")),
                reason=str(request.data.get("reason", "")),
                expires_at=expires_at,
            )
        except ModerationServiceError as exc:
            return Response(
                {"detail": str(exc)}, status=409 if exc.conflict else 400
            )
        return Response(ReportSerializer(report).data)


class StaffReportDismissView(APIView):
    permission_classes = [IsModerator]

    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        try:
            report = dismiss_report(
                report=report,
                moderator=request.user,
                reason=str(request.data.get("reason", "")),
            )
        except ModerationServiceError as exc:
            return Response(
                {"detail": str(exc)}, status=409 if exc.conflict else 400
            )
        return Response(ReportSerializer(report).data)

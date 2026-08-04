import secrets, uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsReviewer
from common.storage.s3 import delete_object, head_object, presign_get, presign_put
from apps.audit.services import audit
from apps.profiles.image_processing import InvalidImage, normalize_private_image

from .models import VerificationRequest, VerificationEvidence
from .services import VerificationActionError, review_verification_request
from .serializers import VerificationRequestSerializer, StaffVerificationSerializer

ALLOWED = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class VerificationCurrentView(APIView):
    def get(self, request):
        obj = VerificationRequest.objects.filter(user=request.user).order_by("-created_at").first()
        return Response(VerificationRequestSerializer(obj).data if obj else None)


class VerificationCreateView(APIView):
    def post(self, request):
        active = VerificationRequest.objects.filter(
            user=request.user,
            status__in=[
                VerificationRequest.Status.DRAFT,
                VerificationRequest.Status.SUBMITTED,
                VerificationRequest.Status.IN_REVIEW,
                VerificationRequest.Status.NEEDS_MORE,
            ],
        ).first()
        if active:
            return Response(VerificationRequestSerializer(active).data)
        obj = VerificationRequest.objects.create(
            user=request.user,
            challenge_code=secrets.token_hex(3).upper(),
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        return Response(VerificationRequestSerializer(obj).data, status=201)


class EvidencePresignView(APIView):
    def post(self, request):
        vr = get_object_or_404(
            VerificationRequest,
            pk=request.data.get("request_id"),
            user=request.user,
            status__in=[VerificationRequest.Status.DRAFT, VerificationRequest.Status.NEEDS_MORE],
        )
        evidence_type = request.data.get("evidence_type")
        content_type = request.data.get("content_type")
        try:
            size = int(request.data.get("size", 0))
        except (TypeError, ValueError):
            size = 0
        if (
            evidence_type not in VerificationEvidence.Type.values
            or content_type not in ALLOWED
            or size <= 0
            or size > 10 * 1024 * 1024
        ):
            return Response({"detail": "File xác minh không hợp lệ."}, status=400)
        key = (
            f"verification/{request.user.pk}/{vr.pk}/{evidence_type}-"
            f"{uuid.uuid4().hex}.{ALLOWED[content_type]}"
        )
        signed = presign_put(settings.S3_VERIFICATION_BUCKET, key, content_type)
        return Response(
            {
                "object_key": key,
                "upload_url": signed.upload_url,
                "headers": signed.headers,
                "expires_in": 600,
            }
        )


class EvidenceCompleteView(APIView):
    def post(self, request):
        vr = get_object_or_404(
            VerificationRequest,
            pk=request.data.get("request_id"),
            user=request.user,
            status__in=[VerificationRequest.Status.DRAFT, VerificationRequest.Status.NEEDS_MORE],
        )
        key = request.data.get("object_key", "")
        evidence_type = request.data.get("evidence_type")
        if (
            not key.startswith(f"verification/{request.user.pk}/{vr.pk}/")
            or evidence_type not in VerificationEvidence.Type.values
        ):
            return Response({"detail": "Dữ liệu không hợp lệ."}, status=400)
        try:
            metadata = head_object(settings.S3_VERIFICATION_BUCKET, key)
            if metadata.get("ContentLength", 0) > 10 * 1024 * 1024:
                raise InvalidImage("File quá lớn.")
            processed = normalize_private_image(settings.S3_VERIFICATION_BUCKET, key)
        except InvalidImage as exc:
            return Response({"detail": str(exc)}, status=400)
        except Exception:
            return Response({"detail": "Không thể xử lý file xác minh."}, status=400)

        previous = VerificationEvidence.objects.filter(
            request=vr, evidence_type=evidence_type
        ).first()
        old_key = previous.private_object_key if previous else ""
        obj, _ = VerificationEvidence.objects.update_or_create(
            request=vr,
            evidence_type=evidence_type,
            defaults={
                "private_object_key": processed["object_key"],
                "mime_type": processed["mime_type"],
                "file_size": processed["file_size"],
                "deleted_at": None,
            },
        )
        if old_key and old_key != obj.private_object_key:
            try:
                delete_object(settings.S3_VERIFICATION_BUCKET, old_key)
            except Exception:
                pass
        return Response({"id": obj.id, "evidence_type": obj.evidence_type}, status=201)


class VerificationSubmitView(APIView):
    def post(self, request, pk):
        vr = get_object_or_404(
            VerificationRequest,
            pk=pk,
            user=request.user,
            status__in=[VerificationRequest.Status.DRAFT, VerificationRequest.Status.NEEDS_MORE],
        )
        required = set(VerificationEvidence.Type.values)
        available = set(
            vr.evidence.filter(deleted_at__isnull=True).values_list(
                "evidence_type", flat=True
            )
        )
        if required - available:
            return Response(
                {
                    "detail": "Cần đủ giấy tờ, selfie và selfie với mã thử thách.",
                    "missing": list(required - available),
                },
                status=400,
            )
        vr.status = VerificationRequest.Status.SUBMITTED
        vr.submitted_at = timezone.now()
        vr.user_visible_reason = ""
        vr.save(
            update_fields=["status", "submitted_at", "user_visible_reason", "updated_at"]
        )
        audit(actor=request.user, action="verification.submitted", target=vr)
        return Response(VerificationRequestSerializer(vr).data)


class StaffVerificationListView(generics.ListAPIView):
    permission_classes = [IsReviewer]
    serializer_class = StaffVerificationSerializer

    def get_queryset(self):
        return (
            VerificationRequest.objects.filter(
                status__in=[
                    VerificationRequest.Status.SUBMITTED,
                    VerificationRequest.Status.IN_REVIEW,
                ]
            )
            .select_related("user__profile")
            .prefetch_related("user__profile__photos", "evidence")
            .order_by("submitted_at")
        )


class StaffVerificationDetailView(APIView):
    permission_classes = [IsReviewer]

    def get(self, request, pk):
        vr = get_object_or_404(
            VerificationRequest.objects.select_related("user__profile").prefetch_related(
                "evidence", "user__profile__photos"
            ),
            pk=pk,
        )
        data = StaffVerificationSerializer(vr).data
        data["evidence_urls"] = [
            {
                "type": evidence.evidence_type,
                "url": presign_get(
                    settings.S3_VERIFICATION_BUCKET,
                    evidence.private_object_key,
                    300,
                ),
            }
            for evidence in vr.evidence.filter(deleted_at__isnull=True)
        ]
        return Response(data)


class StaffVerificationActionView(APIView):
    permission_classes = [IsReviewer]

    def post(self, request, pk):
        vr = get_object_or_404(VerificationRequest, pk=pk)
        try:
            vr = review_verification_request(
                verification_request=vr,
                reviewer=request.user,
                action=str(request.data.get("action", "")),
                reason_code=str(request.data.get("reason_code", "")),
                user_visible_reason=str(request.data.get("user_visible_reason", "")),
                internal_note=str(request.data.get("internal_note", "")),
            )
        except VerificationActionError as exc:
            return Response(
                {"detail": str(exc)}, status=409 if exc.conflict else 400
            )
        return Response(StaffVerificationSerializer(vr).data)

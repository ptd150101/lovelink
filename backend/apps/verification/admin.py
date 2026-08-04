from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from apps.audit.services import audit
from common.storage.s3 import presign_get

from .models import VerificationEvidence, VerificationRequest, VerificationReview
from .services import VerificationActionError, review_verification_request


class EvidenceInline(admin.TabularInline):
    model = VerificationEvidence
    extra = 0
    can_delete = False
    fields = (
        "evidence_type",
        "mime_type",
        "file_size",
        "uploaded_at",
        "deleted_at",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class ReviewInline(admin.TabularInline):
    model = VerificationReview
    extra = 0
    can_delete = False
    fields = (
        "reviewer",
        "action",
        "previous_status",
        "new_status",
        "reason_code",
        "internal_note",
        "created_at",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    change_form_template = "admin/verification/verificationrequest/change_form.html"
    list_display = (
        "user",
        "status",
        "submitted_at",
        "assigned_reviewer",
        "decided_at",
    )
    list_filter = ("status", "submitted_at", "decided_at")
    search_fields = ("user__email", "user__profile__display_name", "challenge_code")
    ordering = ("submitted_at", "created_at")
    inlines = (EvidenceInline, ReviewInline)
    readonly_fields = (
        "id",
        "user",
        "status",
        "challenge_code",
        "submitted_at",
        "review_started_at",
        "decided_at",
        "assigned_reviewer",
        "decision_reason_code",
        "user_visible_reason",
        "internal_note",
        "expires_at",
        "created_at",
        "updated_at",
        "profile_summary",
        "evidence_access",
    )
    fieldsets = (
        (
            "Yêu cầu",
            {
                "fields": (
                    "id",
                    "user",
                    "status",
                    "challenge_code",
                    "submitted_at",
                    "review_started_at",
                    "decided_at",
                    "assigned_reviewer",
                    "expires_at",
                )
            },
        ),
        ("Hồ sơ", {"fields": ("profile_summary",)}),
        ("Bằng chứng riêng tư", {"fields": ("evidence_access",)}),
        (
            "Quyết định gần nhất",
            {
                "fields": (
                    "decision_reason_code",
                    "user_visible_reason",
                    "internal_note",
                )
            },
        ),
        ("Hệ thống", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def _can_review(self, request):
        return request.user.is_superuser or request.user.has_perm(
            "verification.review_verificationrequest"
        )

    def get_urls(self):
        custom = [
            path(
                "<uuid:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="verification_verificationrequest_review",
            ),
            path(
                "evidence/<uuid:evidence_id>/view/",
                self.admin_site.admin_view(self.evidence_view),
                name="verification_verificationevidence_view",
            ),
        ]
        return custom + super().get_urls()

    @admin.display(description="Hồ sơ thành viên")
    def profile_summary(self, obj):
        profile = getattr(obj.user, "profile", None)
        if not profile:
            return "Không có hồ sơ."
        profile_url = reverse("admin:profiles_profile_change", args=[profile.pk])
        photo_count = profile.photos.count()
        return format_html(
            '<a href="{}"><strong>{}</strong></a><br>'
            "Ngày sinh: {} · Giới tính: {} · Ảnh: {} · Tích xanh: {}",
            profile_url,
            profile.display_name or obj.user.email,
            profile.birth_date,
            profile.get_gender_display() or "—",
            photo_count,
            profile.get_verification_level_display(),
        )

    @admin.display(description="Mở bằng chứng")
    def evidence_access(self, obj):
        evidence = obj.evidence.filter(deleted_at__isnull=True).order_by("evidence_type")
        if not evidence:
            return "Chưa có bằng chứng."
        return format_html_join(
            " ",
            '<a class="button" target="_blank" rel="noopener" href="{}">Mở {}</a>',
            (
                (
                    reverse(
                        "admin:verification_verificationevidence_view",
                        args=[item.pk],
                    ),
                    item.get_evidence_type_display(),
                )
                for item in evidence
            ),
        )

    def evidence_view(self, request, evidence_id):
        if not self._can_review(request):
            return HttpResponseForbidden("Bạn không có quyền xem bằng chứng xác minh.")
        evidence = get_object_or_404(
            VerificationEvidence.objects.select_related("request__user"),
            pk=evidence_id,
            deleted_at__isnull=True,
        )
        audit(
            actor=request.user,
            action="verification.evidence_viewed",
            target=evidence,
            after={"request_id": str(evidence.request_id)},
            actor_role="verification_reviewer",
        )
        return redirect(
            presign_get(
                settings.S3_VERIFICATION_BUCKET,
                evidence.private_object_key,
                300,
            )
        )

    def review_view(self, request, object_id):
        if not self._can_review(request):
            return HttpResponseForbidden("Bạn không có quyền xét duyệt xác minh.")
        verification_request = get_object_or_404(VerificationRequest, pk=object_id)
        if request.method != "POST":
            return redirect(
                reverse(
                    "admin:verification_verificationrequest_change",
                    args=[verification_request.pk],
                )
            )
        try:
            review_verification_request(
                verification_request=verification_request,
                reviewer=request.user,
                action=str(request.POST.get("review_action", "")),
                reason_code=str(request.POST.get("reason_code", "")),
                user_visible_reason=str(request.POST.get("user_visible_reason", "")),
                internal_note=str(request.POST.get("internal_note", "")),
            )
        except VerificationActionError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Đã cập nhật kết quả xét duyệt.")
        return redirect(
            reverse(
                "admin:verification_verificationrequest_change",
                args=[verification_request.pk],
            )
        )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context.update(
            {
                "can_review": self._can_review(request),
                "review_action_url": reverse(
                    "admin:verification_verificationrequest_review",
                    args=[object_id],
                )
                if object_id
                else "",
                "review_actions": (
                    ("start", "Bắt đầu xét duyệt"),
                    ("request_more", "Yêu cầu bổ sung"),
                    ("approve", "Phê duyệt và cấp tích xanh"),
                    ("reject", "Từ chối"),
                    ("revoke", "Thu hồi tích xanh"),
                ),
            }
        )
        return super().changeform_view(request, object_id, form_url, extra_context)

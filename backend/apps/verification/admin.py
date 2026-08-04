from __future__ import annotations

from django.conf import settings
from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join

from common.storage.s3 import presign_get

from .models import VerificationEvidence, VerificationRequest, VerificationReview
from .services import VerificationActionError, review_verification_request


def can_review(request):
    return request.user.is_superuser or request.user.has_perm(
        "verification.review_verificationrequest"
    )


class EvidenceInline(admin.TabularInline):
    model = VerificationEvidence
    extra = 0
    can_delete = False
    fields = (
        "evidence_type",
        "open_evidence",
        "mime_type",
        "file_size",
        "uploaded_at",
        "deleted_at",
    )
    readonly_fields = fields

    @admin.display(description="Bằng chứng riêng tư")
    def open_evidence(self, obj):
        if not obj.pk or obj.deleted_at:
            return "Không còn khả dụng"
        try:
            url = presign_get(
                settings.S3_VERIFICATION_BUCKET,
                obj.private_object_key,
                expires=300,
            )
        except Exception:
            return "Không thể tạo liên kết tạm thời"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Mở trong 5 phút</a>',
            url,
        )

    def has_view_permission(self, request, obj=None):
        return can_review(request)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
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

    def has_view_permission(self, request, obj=None):
        return can_review(request)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "submitted_at",
        "assigned_reviewer",
        "decided_at",
        "evidence_count",
    )
    list_filter = ("status", "submitted_at", "decided_at")
    search_fields = ("user__email", "user__profile__display_name", "challenge_code")
    list_select_related = ("user", "assigned_reviewer")
    inlines = (EvidenceInline, ReviewInline)
    actions = (
        "start_review",
        "approve_requests",
        "request_more_information",
        "reject_requests",
        "revoke_verification",
    )
    fields = (
        "user",
        "status",
        "challenge_code",
        "evidence_summary",
        "submitted_at",
        "review_started_at",
        "decided_at",
        "assigned_reviewer",
        "expires_at",
        "decision_reason_code",
        "user_visible_reason",
        "internal_note",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "user",
        "status",
        "challenge_code",
        "evidence_summary",
        "submitted_at",
        "review_started_at",
        "decided_at",
        "assigned_reviewer",
        "expires_at",
        "created_at",
        "updated_at",
    )

    def has_module_permission(self, request):
        return can_review(request)

    def has_view_permission(self, request, obj=None):
        return can_review(request)

    def has_change_permission(self, request, obj=None):
        return can_review(request)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Số bằng chứng")
    def evidence_count(self, obj):
        return obj.evidence.filter(deleted_at__isnull=True).count()

    @admin.display(description="Bằng chứng xác minh")
    def evidence_summary(self, obj):
        links = []
        errors = []
        for evidence in obj.evidence.filter(deleted_at__isnull=True):
            try:
                url = presign_get(
                    settings.S3_VERIFICATION_BUCKET,
                    evidence.private_object_key,
                    expires=300,
                )
                links.append((url, evidence.get_evidence_type_display()))
            except Exception:
                errors.append(evidence.get_evidence_type_display())
        rendered = format_html_join(
            "<br>",
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            links,
        ) if links else ""
        if errors:
            error_text = format_html(
                "<br><span style='color:#b91c1c'>Không tạo được link: {}</span>",
                ", ".join(errors),
            )
            return format_html("{}{}", rendered, error_text)
        return rendered or "Chưa có bằng chứng"

    def _run_action(self, request, queryset, action):
        success = 0
        for obj in queryset.select_related("user__profile"):
            try:
                review_verification_request(
                    verification_request=obj,
                    reviewer=request.user,
                    action=action,
                    reason_code=obj.decision_reason_code,
                    user_visible_reason=obj.user_visible_reason,
                    internal_note=obj.internal_note,
                )
                success += 1
            except VerificationActionError as exc:
                self.message_user(
                    request,
                    f"{obj.user.email}: {exc}",
                    level=messages.ERROR,
                )
        if success:
            self.message_user(
                request,
                f"Đã xử lý {success} yêu cầu xác minh.",
                level=messages.SUCCESS,
            )

    @admin.action(description="Bắt đầu xét duyệt")
    def start_review(self, request, queryset):
        self._run_action(request, queryset, "start")

    @admin.action(description="Phê duyệt và cấp tích xanh")
    def approve_requests(self, request, queryset):
        self._run_action(request, queryset, "approve")

    @admin.action(description="Yêu cầu người dùng bổ sung")
    def request_more_information(self, request, queryset):
        self._run_action(request, queryset, "request_more")

    @admin.action(description="Từ chối xác minh")
    def reject_requests(self, request, queryset):
        self._run_action(request, queryset, "reject")

    @admin.action(description="Thu hồi tích xanh")
    def revoke_verification(self, request, queryset):
        self._run_action(request, queryset, "revoke")

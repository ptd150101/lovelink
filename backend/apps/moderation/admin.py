from django.contrib import admin, messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.dateparse import parse_datetime
from django.utils.html import format_html
from django.utils.timezone import is_naive, make_aware

from apps.calls.models import CallSession
from apps.messaging.models import Message
from apps.profiles.models import ProfilePhoto

from .models import Block, ModerationAction, Report
from .services import (
    ModerationServiceError,
    apply_moderation_action,
    dismiss_report,
)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__email", "blocked__email")
    readonly_fields = ("blocker", "blocked", "created_at")

    def has_add_permission(self, request):
        return False


class ModerationActionInline(admin.TabularInline):
    model = ModerationAction
    extra = 0
    can_delete = False
    fields = ("moderator", "action", "reason", "expires_at", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    change_form_template = "admin/moderation/report/change_form.html"
    list_display = (
        "reported_user",
        "reason_code",
        "target_type",
        "status",
        "assigned_moderator",
        "created_at",
    )
    list_filter = ("status", "reason_code", "target_type", "created_at")
    search_fields = (
        "reported_user__email",
        "reported_user__profile__display_name",
        "reporter__email",
        "description",
        "target_id",
    )
    readonly_fields = (
        "id",
        "reporter",
        "reported_user",
        "target_type",
        "target_id",
        "reason_code",
        "description",
        "status",
        "assigned_moderator",
        "resolution",
        "created_at",
        "resolved_at",
        "target_preview",
    )
    fieldsets = (
        (
            "Báo cáo",
            {
                "fields": (
                    "id",
                    "reporter",
                    "reported_user",
                    "reason_code",
                    "status",
                    "created_at",
                    "description",
                )
            },
        ),
        ("Đối tượng bị báo cáo", {"fields": ("target_type", "target_id", "target_preview")}),
        (
            "Kết quả",
            {"fields": ("assigned_moderator", "resolution", "resolved_at")},
        ),
    )
    inlines = (ModerationActionInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def _can_review(self, request):
        return request.user.is_superuser or request.user.has_perm(
            "moderation.review_report"
        )

    @admin.display(description="Nội dung liên quan")
    def target_preview(self, obj):
        if obj.target_type == Report.Target.PROFILE:
            url = reverse(
                "admin:profiles_profile_change", args=[obj.reported_user.profile.pk]
            )
            return format_html('<a href="{}">Mở hồ sơ người dùng</a>', url)
        if obj.target_type == Report.Target.PHOTO:
            photo = ProfilePhoto.objects.filter(
                pk=obj.target_id, profile__user=obj.reported_user
            ).first()
            if photo:
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener">'
                    '<img src="{}" alt="Ảnh bị báo cáo" style="max-width:240px;max-height:240px;border-radius:8px">'
                    "</a>",
                    photo.public_url,
                    photo.thumbnail_url or photo.public_url,
                )
        if obj.target_type == Report.Target.MESSAGE:
            message = Message.objects.filter(
                pk=obj.target_id, sender=obj.reported_user
            ).first()
            if message:
                return format_html(
                    "<strong>Tin nhắn:</strong><br><pre style='white-space:pre-wrap'>{}</pre>",
                    message.text,
                )
        if obj.target_type == Report.Target.CALL:
            call = CallSession.objects.filter(pk=obj.target_id).first()
            if call:
                return format_html(
                    "Cuộc gọi {} · trạng thái {} · bắt đầu {} · kết thúc {}",
                    call.pk,
                    call.get_status_display(),
                    call.created_at,
                    call.ended_at or "—",
                )
        return "Không tìm thấy đối tượng hoặc đối tượng đã bị xóa."

    def get_urls(self):
        custom = [
            path(
                "<uuid:object_id>/moderate/",
                self.admin_site.admin_view(self.moderate_view),
                name="moderation_report_moderate",
            )
        ]
        return custom + super().get_urls()

    def moderate_view(self, request, object_id):
        if not self._can_review(request):
            return HttpResponseForbidden("Bạn không có quyền xử lý báo cáo.")
        report = get_object_or_404(Report, pk=object_id)
        if request.method != "POST":
            return redirect(reverse("admin:moderation_report_change", args=[report.pk]))
        action = str(request.POST.get("moderation_action", ""))
        reason = str(request.POST.get("reason", ""))
        try:
            if action == "dismiss":
                dismiss_report(report=report, moderator=request.user, reason=reason)
            else:
                expires_at = None
                if request.POST.get("expires_at"):
                    expires_at = parse_datetime(request.POST["expires_at"])
                    if expires_at and is_naive(expires_at):
                        expires_at = make_aware(expires_at)
                    if expires_at is None:
                        raise ModerationServiceError("Thời hạn không hợp lệ.")
                apply_moderation_action(
                    report=report,
                    moderator=request.user,
                    action=action,
                    reason=reason,
                    expires_at=expires_at,
                )
        except ModerationServiceError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Đã cập nhật kết quả xử lý báo cáo.")
        return redirect(reverse("admin:moderation_report_change", args=[report.pk]))

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context.update(
            {
                "can_review": self._can_review(request),
                "moderation_action_url": reverse(
                    "admin:moderation_report_moderate", args=[object_id]
                )
                if object_id
                else "",
                "moderation_actions": tuple(ModerationAction.Action.choices)
                + (("dismiss", "Bỏ qua báo cáo"),),
            }
        )
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ("target_user", "action", "moderator", "created_at", "expires_at")
    list_filter = ("action", "created_at")
    search_fields = ("target_user__email", "moderator__email", "reason")
    readonly_fields = [field.name for field in ModerationAction._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

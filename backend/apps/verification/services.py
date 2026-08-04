from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.audit.services import audit
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from apps.profiles.models import Profile

from .models import VerificationRequest, VerificationReview


@dataclass(frozen=True)
class VerificationActionError(Exception):
    message: str
    conflict: bool = False

    def __str__(self) -> str:
        return self.message


ACTION_STATUS = {
    "start": VerificationRequest.Status.IN_REVIEW,
    "request_more": VerificationRequest.Status.NEEDS_MORE,
    "approve": VerificationRequest.Status.VERIFIED,
    "reject": VerificationRequest.Status.REJECTED,
    "revoke": VerificationRequest.Status.REVOKED,
}

ALLOWED_FROM = {
    "start": {VerificationRequest.Status.SUBMITTED, VerificationRequest.Status.IN_REVIEW},
    "request_more": {VerificationRequest.Status.SUBMITTED, VerificationRequest.Status.IN_REVIEW},
    "approve": {VerificationRequest.Status.SUBMITTED, VerificationRequest.Status.IN_REVIEW},
    "reject": {VerificationRequest.Status.SUBMITTED, VerificationRequest.Status.IN_REVIEW},
    "revoke": {VerificationRequest.Status.VERIFIED},
}

REASON_REQUIRED = {"request_more", "reject", "revoke"}


def review_verification_request(
    *,
    verification_request: VerificationRequest,
    reviewer,
    action: str,
    reason_code: str = "",
    user_visible_reason: str = "",
    internal_note: str = "",
) -> VerificationRequest:
    if action not in ACTION_STATUS:
        raise VerificationActionError("Hành động xác minh không hợp lệ.")
    if not reviewer.has_perm("verification.review_verificationrequest") and not reviewer.is_superuser:
        raise VerificationActionError("Bạn không có quyền xét duyệt hồ sơ xác minh.")

    reason_code = reason_code.strip()
    user_visible_reason = user_visible_reason.strip()
    internal_note = internal_note.strip()
    if action in REASON_REQUIRED and (not reason_code or not user_visible_reason):
        raise VerificationActionError(
            "Hành động này cần mã lý do và nội dung phản hồi cho người dùng."
        )

    with transaction.atomic():
        locked = (
            VerificationRequest.objects.select_for_update()
            .select_related("user__profile")
            .get(pk=verification_request.pk)
        )
        previous_status = locked.status
        if previous_status not in ALLOWED_FROM[action]:
            raise VerificationActionError(
                "Trạng thái hiện tại không cho phép thực hiện hành động này.",
                conflict=True,
            )

        new_status = ACTION_STATUS[action]
        locked.status = new_status
        locked.assigned_reviewer = reviewer
        locked.decision_reason_code = reason_code
        locked.user_visible_reason = user_visible_reason
        locked.internal_note = internal_note

        now = timezone.now()
        if action == "start" and not locked.review_started_at:
            locked.review_started_at = now
        if action in {"approve", "reject", "revoke"}:
            locked.decided_at = now
        locked.save()

        VerificationReview.objects.create(
            request=locked,
            reviewer=reviewer,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            reason_code=reason_code,
            internal_note=internal_note,
        )

        profile = locked.user.profile
        notification_type = None
        notification_title = ""
        notification_body = user_visible_reason

        if action == "approve":
            profile.verification_level = Profile.VerificationLevel.IDENTITY
            profile.verified_at = now
            profile.save(update_fields=["verification_level", "verified_at", "updated_at"])
            notification_type = Notification.Type.VERIFICATION_APPROVED
            notification_title = "Xác minh danh tính thành công"
            notification_body = (
                user_visible_reason
                or "Danh tính của bạn đã được đội ngũ LoveLink xác minh."
            )
        elif action == "request_more":
            notification_type = Notification.Type.VERIFICATION_NEEDS_MORE
            notification_title = "Cần bổ sung hồ sơ xác minh"
        elif action == "reject":
            notification_type = Notification.Type.VERIFICATION_REJECTED
            notification_title = "Hồ sơ xác minh chưa được chấp nhận"
        elif action == "revoke":
            profile.verification_level = Profile.VerificationLevel.REVOKED
            profile.verified_at = None
            profile.save(update_fields=["verification_level", "verified_at", "updated_at"])
            notification_type = Notification.Type.ACCOUNT_WARNING
            notification_title = "Tích xanh đã được thu hồi"

        audit(
            actor=reviewer,
            action=f"verification.{action}",
            target=locked,
            before={"status": previous_status},
            after={"status": new_status, "reason": reason_code},
            actor_role="verification_reviewer",
        )

    if notification_type:
        push_notification(
            user=locked.user,
            type=notification_type,
            title=notification_title,
            body=notification_body,
            entity=locked,
        )
    return locked

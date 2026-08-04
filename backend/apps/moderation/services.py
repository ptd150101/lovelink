from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import audit
from apps.notifications.models import Notification
from apps.notifications.services import push_notification
from apps.profiles.models import Profile, ProfilePhoto

from .models import Block, ModerationAction, Report


def are_blocked(a, b):
    return Block.objects.filter(
        Q(blocker=a, blocked=b) | Q(blocker=b, blocked=a)
    ).exists()


def blocked_user_ids(user):
    ids = set()
    for blocker_id, blocked_id in Block.objects.filter(
        Q(blocker=user) | Q(blocked=user)
    ).values_list("blocker_id", "blocked_id"):
        ids.add(blocked_id if blocker_id == user.id else blocker_id)
    return ids


class ModerationServiceError(Exception):
    def __init__(self, message: str, conflict: bool = False):
        super().__init__(message)
        self.message = message
        self.conflict = conflict

    def __str__(self):
        return self.message


def _require_moderator(moderator):
    if not (
        moderator.is_superuser or moderator.has_perm("moderation.review_report")
    ):
        raise ModerationServiceError("Bạn không có quyền xử lý báo cáo.")


def _push_account_event(user, event):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"user_{user.pk}",
        {
            "type": "app.event",
            "event": event,
            "payload": {"status": user.status},
        },
    )


def apply_moderation_action(
    *,
    report: Report,
    moderator,
    action: str,
    reason: str,
    expires_at=None,
) -> Report:
    _require_moderator(moderator)
    reason = reason.strip()
    if action not in ModerationAction.Action.values or not reason:
        raise ModerationServiceError("Hành động và lý do là bắt buộc.")

    with transaction.atomic():
        locked = (
            Report.objects.select_for_update()
            .select_related("reported_user__profile")
            .get(pk=report.pk)
        )
        if locked.status in {Report.Status.ACTION, Report.Status.DISMISSED}:
            raise ModerationServiceError(
                "Báo cáo này đã được xử lý.", conflict=True
            )

        target = locked.reported_user
        profile = target.profile
        ModerationAction.objects.create(
            moderator=moderator,
            target_user=target,
            report=locked,
            action=action,
            reason=reason,
            expires_at=expires_at,
        )

        if action == ModerationAction.Action.WARN:
            push_notification(
                user=target,
                type=Notification.Type.ACCOUNT_WARNING,
                title="Cảnh báo tài khoản",
                body=reason,
                entity=locked,
            )
        elif action == ModerationAction.Action.HIDE_PROFILE:
            profile.visibility_status = Profile.Visibility.HIDDEN_MOD
            profile.save(update_fields=["visibility_status", "updated_at"])
        elif action == ModerationAction.Action.HIDE_PHOTO:
            updated = ProfilePhoto.objects.filter(
                pk=locked.target_id, profile__user=target
            ).update(moderation_status=ProfilePhoto.Moderation.REJECTED)
            if not updated:
                raise ModerationServiceError(
                    "Không tìm thấy ảnh thuộc báo cáo này."
                )
        elif action == ModerationAction.Action.SUSPEND:
            target.status = target.Status.SUSPENDED
            target.save(update_fields=["status", "updated_at"])
            profile.visibility_status = Profile.Visibility.SUSPENDED
            profile.save(update_fields=["visibility_status", "updated_at"])
            _push_account_event(target, "account.suspended")
        elif action == ModerationAction.Action.BAN:
            target.status = target.Status.BANNED
            target.is_active = False
            target.save(update_fields=["status", "is_active", "updated_at"])
            profile.visibility_status = Profile.Visibility.SUSPENDED
            profile.save(update_fields=["visibility_status", "updated_at"])
            _push_account_event(target, "account.suspended")
        elif action == ModerationAction.Action.REVOKE_BADGE:
            profile.verification_level = Profile.VerificationLevel.REVOKED
            profile.verified_at = None
            profile.save(
                update_fields=["verification_level", "verified_at", "updated_at"]
            )
        elif action == ModerationAction.Action.RESTORE:
            target.status = target.Status.ACTIVE
            target.is_active = True
            target.save(update_fields=["status", "is_active", "updated_at"])
            profile.visibility_status = Profile.Visibility.PUBLISHED
            profile.save(update_fields=["visibility_status", "updated_at"])

        locked.status = Report.Status.ACTION
        locked.resolution = reason
        locked.assigned_moderator = moderator
        locked.resolved_at = timezone.now()
        locked.save(
            update_fields=[
                "status",
                "resolution",
                "assigned_moderator",
                "resolved_at",
            ]
        )
        audit(
            actor=moderator,
            action=f"moderation.{action}",
            target=target,
            after={"reason": reason, "report": str(locked.pk)},
            actor_role="moderator",
        )
    return locked


def dismiss_report(*, report: Report, moderator, reason: str) -> Report:
    _require_moderator(moderator)
    reason = reason.strip() or "Không phát hiện vi phạm."
    with transaction.atomic():
        locked = Report.objects.select_for_update().get(pk=report.pk)
        if locked.status in {Report.Status.ACTION, Report.Status.DISMISSED}:
            raise ModerationServiceError(
                "Báo cáo này đã được xử lý.", conflict=True
            )
        locked.status = Report.Status.DISMISSED
        locked.resolution = reason
        locked.assigned_moderator = moderator
        locked.resolved_at = timezone.now()
        locked.save(
            update_fields=[
                "status",
                "resolution",
                "assigned_moderator",
                "resolved_at",
            ]
        )
        audit(
            actor=moderator,
            action="report.dismissed",
            target=locked,
            after={"reason": reason},
            actor_role="moderator",
        )
    return locked

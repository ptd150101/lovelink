import pytest

from django.contrib.auth.models import Permission
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.notifications.models import Notification
from apps.profiles.models import Profile
from apps.verification.models import VerificationRequest, VerificationReview
from apps.verification.services import VerificationActionError, review_verification_request


@pytest.mark.django_db
def test_reviewer_approval_sets_badge_and_audit(user_factory):
    member = user_factory("verify-member@example.com")
    reviewer = user_factory("verify-reviewer@example.com")
    reviewer.is_staff = True
    reviewer.save(update_fields=["is_staff"])
    reviewer.user_permissions.add(
        Permission.objects.get(codename="review_verificationrequest")
    )
    verification = VerificationRequest.objects.create(
        user=member,
        status=VerificationRequest.Status.SUBMITTED,
        challenge_code="ABC123",
        submitted_at=timezone.now(),
    )

    result = review_verification_request(
        verification_request=verification,
        reviewer=reviewer,
        action="approve",
    )

    member.profile.refresh_from_db()
    assert result.status == VerificationRequest.Status.VERIFIED
    assert member.profile.verification_level == Profile.VerificationLevel.IDENTITY
    assert member.profile.verified_at is not None
    assert VerificationReview.objects.filter(request=verification, action="approve").exists()
    assert AuditLog.objects.filter(target_id=str(verification.pk), action="verification.approve").exists()
    assert Notification.objects.filter(
        user=member, type=Notification.Type.VERIFICATION_APPROVED
    ).exists()


@pytest.mark.django_db
def test_reviewer_rejection_requires_visible_reason(user_factory):
    member = user_factory("reject-member@example.com")
    reviewer = user_factory("reject-reviewer@example.com")
    reviewer.is_staff = True
    reviewer.save(update_fields=["is_staff"])
    reviewer.user_permissions.add(
        Permission.objects.get(codename="review_verificationrequest")
    )
    verification = VerificationRequest.objects.create(
        user=member,
        status=VerificationRequest.Status.SUBMITTED,
        challenge_code="ABC123",
        submitted_at=timezone.now(),
    )

    with pytest.raises(VerificationActionError):
        review_verification_request(
            verification_request=verification,
            reviewer=reviewer,
            action="reject",
        )

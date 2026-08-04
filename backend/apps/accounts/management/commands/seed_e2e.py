from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.connections.models import ConnectionRequest
from apps.messaging.models import Conversation, ConversationMember, Message
from apps.moderation.models import Report
from apps.profiles.models import OccupationCategory, Profile, Province
from apps.verification.models import VerificationRequest


class Command(BaseCommand):
    help = "Create deterministic accounts and workflows for full-stack E2E tests."

    def handle(self, *args, **options):
        user_model = get_user_model()
        province = Province.objects.first()
        occupation = OccupationCategory.objects.first()
        if not province or not occupation:
            raise RuntimeError("Reference data is missing. Run seed_reference_data first.")

        users = []
        definitions = [
            ("e2e.a@lovelink.local", "An", Profile.Gender.MALE, date(1997, 1, 1)),
            ("e2e.b@lovelink.local", "Bình", Profile.Gender.FEMALE, date(1998, 2, 2)),
        ]
        for email, name, gender, birth_date in definitions:
            user, _ = user_model.objects.get_or_create(email=email)
            user.status = user_model.Status.ACTIVE
            user.is_active = True
            user.is_email_verified = True
            user.set_password("E2EPassword123!")
            user.save()
            profile, _ = Profile.objects.get_or_create(
                user=user, defaults={"birth_date": birth_date}
            )
            profile.birth_date = birth_date
            profile.display_name = name
            profile.gender = gender
            profile.interested_genders = [
                Profile.Gender.FEMALE
                if gender == Profile.Gender.MALE
                else Profile.Gender.MALE
            ]
            profile.current_province = province
            profile.hometown_province = province
            profile.height_cm = 172 if gender == Profile.Gender.MALE else 162
            profile.occupation_category = occupation
            profile.occupation_text = "Kỹ sư phần mềm"
            profile.education_level = Profile.Education.UNIVERSITY
            profile.relationship_status = Profile.RelationshipStatus.SINGLE
            profile.relationship_goal = Profile.Goal.SERIOUS
            profile.bio = (
                "Tôi là một người chân thành, thích đọc sách, du lịch và mong muốn "
                "xây dựng một mối quan hệ nghiêm túc lâu dài."
            )
            profile.looking_for = "Một người tôn trọng, biết lắng nghe và tử tế."
            profile.visibility_status = Profile.Visibility.PUBLISHED
            profile.completion_percent = 95
            profile.save()
            users.append(user)

        first, second = users
        connection, _ = ConnectionRequest.objects.get_or_create(
            sender=first,
            receiver=second,
            defaults={
                "intro_message": "Chào bạn, mình muốn làm quen.",
                "status": ConnectionRequest.Status.ACCEPTED,
                "expires_at": timezone.now() + timezone.timedelta(days=30),
            },
        )
        connection.status = ConnectionRequest.Status.ACCEPTED
        if not connection.expires_at:
            connection.expires_at = timezone.now() + timezone.timedelta(days=30)
        connection.save(update_fields=["status", "expires_at"])
        conversation, _ = Conversation.objects.get_or_create(
            connection_request=connection
        )
        ConversationMember.objects.get_or_create(conversation=conversation, user=first)
        ConversationMember.objects.get_or_create(conversation=conversation, user=second)
        Message.objects.get_or_create(
            conversation=conversation,
            sender=first,
            client_message_id="11111111-1111-1111-1111-111111111111",
            defaults={"text": "Tin nhắn khởi tạo cho E2E."},
        )

        verification, _ = VerificationRequest.objects.get_or_create(
            user=second,
            status=VerificationRequest.Status.SUBMITTED,
            defaults={"challenge_code": "E2E123"},
        )
        verification.status = VerificationRequest.Status.SUBMITTED
        verification.save(update_fields=["status"])

        Report.objects.get_or_create(
            reporter=first,
            reported_user=second,
            target_type=Report.Target.PROFILE,
            target_id=str(second.profile.public_id),
            reason_code=Report.Reason.FAKE,
            defaults={"description": "Báo cáo mẫu cho E2E admin."},
        )

        admin, _ = user_model.objects.get_or_create(email="e2e.admin@lovelink.local")
        admin.status = user_model.Status.ACTIVE
        admin.is_active = True
        admin.is_email_verified = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("E2EAdminPassword123!")
        admin.save()

        self.stdout.write(
            self.style.SUCCESS(
                "E2E seed ready: e2e.a/e2e.b password E2EPassword123!, "
                "admin e2e.admin@lovelink.local password E2EAdminPassword123!"
            )
        )

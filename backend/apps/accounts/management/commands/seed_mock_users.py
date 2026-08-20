import uuid
from datetime import date, timedelta
from time import monotonic

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.profiles.models import Interest, OccupationCategory, Profile, ProfilePhoto, Province

MOCK_PASSWORD = "MockPassword123!"
MOCK_EMAIL_PREFIX = "mock."
MOCK_NAMESPACE = uuid.UUID("c43aeaad-9621-4d07-bcc9-d0bb7e69b898")

SURNAMES = (
    "Nguyễn",
    "Trần",
    "Lê",
    "Phạm",
    "Hoàng",
    "Huỳnh",
    "Phan",
    "Vũ",
    "Võ",
    "Đặng",
    "Bùi",
    "Đỗ",
    "Hồ",
    "Ngô",
    "Dương",
)
MIDDLE_NAMES = ("Minh", "Ngọc", "Thanh", "Gia", "Khánh", "Quỳnh", "Đức", "Hoài", "Tuấn", "Mai")
GIVEN_NAMES = (
    "An",
    "Anh",
    "Bình",
    "Chi",
    "Dũng",
    "Giang",
    "Hà",
    "Hải",
    "Hân",
    "Hùng",
    "Hương",
    "Khang",
    "Lan",
    "Linh",
    "Long",
    "Mai",
    "Nam",
    "Ngân",
    "Nhi",
    "Phong",
    "Phúc",
    "Quân",
    "Thảo",
    "Trang",
    "Trung",
    "Vy",
)
JOB_TITLES = (
    "Kỹ sư phần mềm",
    "Chuyên viên kinh doanh",
    "Nhân viên ngân hàng",
    "Giáo viên",
    "Bác sĩ",
    "Kỹ sư",
    "Thiết kế đồ họa",
    "Chuyên viên pháp lý",
    "Marketing",
    "Nhân viên văn phòng",
    "Freelancer",
    "Sinh viên",
)
BIOS = (
    "Thích cà phê, du lịch và những cuộc trò chuyện chân thành.",
    "Yêu công việc, thích chạy bộ và khám phá những quán ăn mới.",
    "Hướng nội vừa đủ, vui tính đúng lúc, đang tìm một mối quan hệ nghiêm túc.",
    "Cuối tuần thường đọc sách, xem phim hoặc đi đâu đó quanh thành phố.",
    "Ưu tiên sự tử tế, rõ ràng và tôn trọng trong một mối quan hệ.",
)
LOOKING_FOR = (
    "Một người chân thành, biết lắng nghe và nghiêm túc khi tìm hiểu.",
    "Người có cùng giá trị sống và sẵn sàng cùng nhau trải nghiệm điều mới.",
    "Một mối quan hệ ổn định, tôn trọng không gian riêng của nhau.",
)


class Command(BaseCommand):
    help = "Generate a deterministic large local dataset of mock LoveLink users and profiles."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1_000_000)
        parser.add_argument("--start-index", type=int, default=1)
        parser.add_argument("--batch-size", type=int, default=5_000)
        parser.add_argument(
            "--with-interests",
            action="store_true",
            help="Attach three deterministic interests to every generated profile.",
        )
        parser.add_argument(
            "--with-photos",
            action="store_true",
            help="Add one deterministic external placeholder portrait per profile.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete every account whose email starts with mock. before returning.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_mock_users is restricted to DEBUG/local environments.")

        user_model = get_user_model()
        if options["clear"]:
            deleted, _ = user_model.objects.filter(email__startswith=MOCK_EMAIL_PREFIX).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted:,} mock rows."))
            return

        count = options["count"]
        start_index = options["start_index"]
        batch_size = options["batch_size"]
        if count <= 0:
            raise CommandError("--count must be greater than zero.")
        if start_index <= 0:
            raise CommandError("--start-index must be greater than zero.")
        if batch_size <= 0:
            raise CommandError("--batch-size must be greater than zero.")

        provinces = list(
            Province.objects.order_by("sort_order", "code").values_list("code", flat=True)
        )
        occupations = list(
            OccupationCategory.objects.filter(is_active=True)
            .order_by("name")
            .values_list("id", flat=True)
        )
        interests = list(
            Interest.objects.filter(is_active=True).order_by("name").values_list("id", flat=True)
        )
        if not provinces or not occupations:
            raise CommandError("Reference data is missing. Run seed_reference_data first.")
        if options["with_interests"] and len(interests) < 3:
            raise CommandError("At least three interests are required for --with-interests.")

        password_hash = make_password(MOCK_PASSWORD)
        now = timezone.now()
        today = timezone.localdate()
        profile_interest_model = Profile.interests.through
        started = monotonic()

        for offset in range(0, count, batch_size):
            size = min(batch_size, count - offset)
            users = []
            profiles = []
            profile_interests = []
            photos = []

            for step in range(size):
                index = start_index + offset + step
                user_id = self._uuid("user", index)
                profile_id = self._uuid("profile", index)
                gender = self._gender(index)
                created_at = now - timedelta(days=index % 1_825)
                last_seen_at = now - timedelta(
                    days=index % 90,
                    minutes=(index * 17) % 1_440,
                )
                email = f"{MOCK_EMAIL_PREFIX}{index:09d}@lovelink.local"

                users.append(
                    user_model(
                        id=user_id,
                        email=email,
                        password=password_hash,
                        status=user_model.Status.ACTIVE,
                        is_active=True,
                        is_email_verified=True,
                        is_phone_verified=index % 3 == 0,
                        last_seen_at=last_seen_at,
                        created_at=created_at,
                        updated_at=now,
                        date_joined=created_at,
                    )
                )

                age = 18 + index % 43
                birth_month = index % 12 + 1
                birth_day = index % 28 + 1
                birth_year = today.year - age
                if (birth_month, birth_day) > (today.month, today.day):
                    birth_year -= 1
                birth_date = date(birth_year, birth_month, birth_day)
                published = index % 20 != 0
                profiles.append(
                    Profile(
                        id=profile_id,
                        public_id=self._uuid("public", index),
                        user_id=user_id,
                        display_name=self._name(index),
                        birth_date=birth_date,
                        gender=gender,
                        interested_genders=self._interested_genders(gender),
                        current_province_id=provinces[index % len(provinces)],
                        hometown_province_id=provinces[(index * 7) % len(provinces)],
                        height_cm=150 + index % 46,
                        occupation_category_id=occupations[index % len(occupations)],
                        occupation_text=JOB_TITLES[index % len(JOB_TITLES)],
                        education_level=self._choice(Profile.Education.values, index, 3),
                        income_band=self._choice(Profile.Income.values, index, 5),
                        relationship_status=self._choice(
                            Profile.RelationshipStatus.values, index, 7
                        ),
                        relationship_goal=self._choice(Profile.Goal.values, index, 11),
                        religion=("", "Không", "Phật giáo", "Công giáo")[index % 4],
                        smoking_status=self._choice(Profile.Habit.values, index, 13),
                        drinking_status=self._choice(Profile.Habit.values, index, 17),
                        children_status=self._choice(Profile.Children.values, index, 19),
                        children_plan=self._choice(Profile.ChildrenPlan.values, index, 23),
                        bio=BIOS[index % len(BIOS)],
                        looking_for=LOOKING_FOR[index % len(LOOKING_FOR)],
                        field_visibility={},
                        visibility_status=(
                            Profile.Visibility.PUBLISHED
                            if published
                            else Profile.Visibility.HIDDEN_USER
                        ),
                        completion_percent=80 + index % 21,
                        verification_level=(
                            Profile.VerificationLevel.IDENTITY
                            if index % 5 == 0
                            else Profile.VerificationLevel.NONE
                        ),
                        verified_at=last_seen_at if index % 5 == 0 else None,
                        published_at=created_at if published else None,
                        created_at=created_at,
                        updated_at=now,
                    )
                )

                if options["with_interests"]:
                    selected = {
                        interests[index % len(interests)],
                        interests[(index + 5) % len(interests)],
                        interests[(index + 11) % len(interests)],
                    }
                    for interest_id in selected:
                        profile_interests.append(
                            profile_interest_model(
                                profile_id=profile_id,
                                interest_id=interest_id,
                            )
                        )

                if options["with_photos"]:
                    portrait_gender = "men" if gender == Profile.Gender.MALE else "women"
                    portrait_number = index % 100
                    photos.append(
                        ProfilePhoto(
                            id=self._uuid("photo", index),
                            profile_id=profile_id,
                            object_key=f"mock/{index:09d}/primary.jpg",
                            public_url=(
                                "https://randomuser.me/api/portraits/"
                                f"{portrait_gender}/{portrait_number}.jpg"
                            ),
                            thumbnail_object_key="",
                            thumbnail_url="",
                            position=0,
                            is_primary=True,
                            moderation_status=ProfilePhoto.Moderation.APPROVED,
                            width=480,
                            height=600,
                            mime_type="image/jpeg",
                            file_size=0,
                            created_at=created_at,
                        )
                    )

            with transaction.atomic():
                user_model.objects.bulk_create(
                    users,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )
                Profile.objects.bulk_create(
                    profiles,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )
                if profile_interests:
                    profile_interest_model.objects.bulk_create(
                        profile_interests,
                        batch_size=batch_size * 3,
                        ignore_conflicts=True,
                    )
                if photos:
                    ProfilePhoto.objects.bulk_create(
                        photos,
                        batch_size=batch_size,
                        ignore_conflicts=True,
                    )

            processed = offset + size
            if processed == count or processed % (batch_size * 10) == 0:
                elapsed = monotonic() - started
                rate = processed / elapsed if elapsed else 0
                self.stdout.write(
                    f"Processed {processed:,}/{count:,} users ({rate:,.0f} users/s)"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Mock seed complete: {count:,} deterministic users starting at "
                f"{start_index:,}. Password: {MOCK_PASSWORD}"
            )
        )

    @staticmethod
    def _uuid(kind, index):
        return uuid.uuid5(MOCK_NAMESPACE, f"{kind}:{index}")

    @staticmethod
    def _choice(values, index, multiplier):
        return values[(index * multiplier) % len(values)]

    @staticmethod
    def _gender(index):
        bucket = index % 100
        if bucket < 49:
            return Profile.Gender.MALE
        if bucket < 98:
            return Profile.Gender.FEMALE
        if bucket == 98:
            return Profile.Gender.NON_BINARY
        return Profile.Gender.OTHER

    @staticmethod
    def _interested_genders(gender):
        if gender == Profile.Gender.MALE:
            return [Profile.Gender.FEMALE]
        if gender == Profile.Gender.FEMALE:
            return [Profile.Gender.MALE]
        return [Profile.Gender.MALE, Profile.Gender.FEMALE]

    @staticmethod
    def _name(index):
        surname = SURNAMES[index % len(SURNAMES)]
        middle = MIDDLE_NAMES[(index * 3) % len(MIDDLE_NAMES)]
        given = GIVEN_NAMES[(index * 7) % len(GIVEN_NAMES)]
        return f"{surname} {middle} {given}"

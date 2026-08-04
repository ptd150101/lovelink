from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.mfa import encrypt_secret, generate_secret, provisioning_uri
from apps.accounts.models import StaffTotpDevice


class Command(BaseCommand):
    help = "Enroll or replace a staff member's TOTP authenticator device."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace an existing active device.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        user = user_model.objects.filter(email=options["email"].lower()).first()
        if not user:
            raise CommandError("Không tìm thấy tài khoản.")
        if not user.is_staff:
            raise CommandError("Tài khoản không phải tài khoản nhân viên.")
        existing = StaffTotpDevice.objects.filter(user=user).first()
        if existing and existing.is_active and not options["replace"]:
            raise CommandError(
                "Tài khoản đã có MFA. Dùng --replace để thay thiết bị."
            )

        secret = generate_secret()
        device, _ = StaffTotpDevice.objects.update_or_create(
            user=user,
            defaults={
                "encrypted_secret": encrypt_secret(secret),
                "is_active": True,
                "confirmed_at": timezone.now(),
                "last_used_step": -1,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Đã bật MFA cho {user.email}."))
        self.stdout.write("Thêm URI sau vào ứng dụng Authenticator:")
        self.stdout.write(provisioning_uri(user.email, secret))
        self.stdout.write(
            self.style.WARNING(
                "URI chỉ được hiển thị lần này. Không lưu vào log hoặc mã nguồn."
            )
        )

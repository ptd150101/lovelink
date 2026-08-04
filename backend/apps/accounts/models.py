import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True
    def create_user(self, email, password=None, **extra_fields):
        if not email: raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password); user.save(using=self._db); return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True); extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True); extra_fields.setdefault("status", User.Status.ACTIVE)
        extra_fields.setdefault("is_email_verified", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Status(models.TextChoices):
        PENDING = "pending_verification", "Chờ xác minh"
        ACTIVE = "active", "Hoạt động"
        SUSPENDED = "suspended", "Đình chỉ"
        BANNED = "banned", "Cấm"
        SCHEDULED_DELETION = "scheduled_for_deletion", "Chờ xóa"
        DELETED = "deleted", "Đã xóa"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_deletion_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tracked_sessions")
    session_key = models.CharField(max_length=64, unique=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
    email_connection_notifications = models.BooleanField(default=True)
    email_message_notifications = models.BooleanField(default=False)
    email_verification_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    show_online_status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

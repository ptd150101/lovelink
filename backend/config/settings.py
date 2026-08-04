from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)

def env_bool(name: str, default: bool = False) -> bool:
    return env(name, str(default)).lower() in {"1", "true", "yes", "on"}

SECRET_KEY = env("DJANGO_SECRET_KEY", "unsafe-development-secret")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [x.strip() for x in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
APP_URL = env("APP_URL", "http://localhost:3000")
API_URL = env("API_URL", "http://localhost:8000")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "channels",
    "apps.accounts",
    "apps.profiles",
    "apps.connections",
    "apps.messaging",
    "apps.calls",
    "apps.verification",
    "apps.moderation",
    "apps.notifications",
    "apps.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.audit.middleware.RequestAuditContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "lovelink"),
        "USER": env("POSTGRES_USER", "lovelink"),
        "PASSWORD": env("POSTGRES_PASSWORD", "lovelink"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = [x.strip() for x in env("CSRF_TRUSTED_ORIGINS", APP_URL).split(",") if x.strip()]
CORS_ALLOWED_ORIGINS = [APP_URL]
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["common.permissions.IsActiveAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.CursorPagination",
    "PAGE_SIZE": 24,
    "EXCEPTION_HANDLER": "common.exceptions.exception_handler",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "2000/hour", "auth": "20/min", "intro": "20/day", "message": "120/min"},
}

REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [REDIS_URL]}}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_BEAT_SCHEDULE = {
    "expire-connection-requests": {"task": "apps.connections.tasks.expire_connection_requests", "schedule": 3600},
    "expire-ringing-calls": {"task": "apps.calls.tasks.expire_ringing_calls", "schedule": 60},
    "purge-verification-evidence": {"task": "apps.verification.tasks.purge_expired_evidence", "schedule": 86400},
    "finalize-account-deletions": {"task": "apps.accounts.tasks.finalize_account_deletions", "schedule": 86400},
}

EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "LoveLink <noreply@lovelink.local>")

S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", "http://localhost:9000")
S3_PUBLIC_ENDPOINT_URL = env("S3_PUBLIC_ENDPOINT_URL", S3_ENDPOINT_URL)
S3_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY", "minioadmin")
S3_PROFILE_BUCKET = env("S3_PROFILE_BUCKET", "profile-media")
S3_VERIFICATION_BUCKET = env("S3_VERIFICATION_BUCKET", "verification-evidence-private")
S3_REGION = env("S3_REGION", "auto")

LIVEKIT_URL = env("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = env("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = env("LIVEKIT_API_SECRET", "devsecret")

EMAIL_VERIFY_MAX_AGE = 60 * 60 * 24
PASSWORD_RESET_MAX_AGE = 60 * 30
CONNECTION_REQUEST_TTL_DAYS = 14
ACCOUNT_DELETION_GRACE_DAYS = 14
VERIFICATION_EVIDENCE_RETENTION_DAYS = 30

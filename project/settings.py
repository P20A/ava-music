"""
Django settings for AVA Music Archive.

The file follows the structure of the official ParsPack Django sample
(https://github.com/parspack-paas/django): `requirements.txt` and `manage.py`
live in the repository root and the WSGI application is
`project.wsgi:application`.

All deployment-specific values are read from environment variables.  See
`.env.example` and `README.md`.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


DEBUG = env_bool("DEBUG", True)

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-secret-key-change-me"
    else:
        raise RuntimeError(
            "SECRET_KEY is required when DEBUG=False. Set it in the PaaS "
            "environment variables (ParsPack provides `django_secret_key`)."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
if not DEBUG and ALLOWED_HOSTS == ["localhost", "127.0.0.1", "testserver"]:
    # Keep the container bootable but make the misconfiguration obvious in logs.
    import logging

    logging.getLogger(__name__).warning(
        "ALLOWED_HOSTS is still the development default while DEBUG=False. "
        "Set ALLOWED_HOSTS to your real domain(s)."
    )

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "").strip().rstrip("/")
ADMIN_URL = "/" + os.environ.get("ADMIN_URL", "admin/").strip().strip("/") + "/"
if ADMIN_URL == "//":
    ADMIN_URL = "/admin/"

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    # Local apps
    "apps.core",
    "apps.users",
    "apps.artists",
    "apps.categories",
    "apps.music",
    "apps.albums",
    "apps.playlists",
    "apps.advertisements",
    "apps.submissions",
    "apps.analytics",
    "apps.seo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RedirectMiddleware",
    "apps.core.middleware.MaintenanceModeMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"
ASGI_APPLICATION = "project.asgi.application"

# ---------------------------------------------------------------------------
# Database - PostgreSQL on ParsPack, SQLite for local development/tests
# ---------------------------------------------------------------------------
def database_from_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("Only PostgreSQL DATABASE_URL values are supported.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or "5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"connect_timeout": env_int("DB_CONNECT_TIMEOUT", 10)},
    }


DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").strip().lower()

if DATABASE_URL:
    DATABASES = {"default": database_from_url(DATABASE_URL)}
elif DB_ENGINE in {"postgres", "postgresql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "ava_music"),
            "USER": os.environ.get("POSTGRES_USER", "user"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {"connect_timeout": env_int("DB_CONNECT_TIMEOUT", 10)},
        }
    }
else:
    sqlite_path = os.environ.get("SQLITE_PATH", str(BASE_DIR / "db.sqlite3"))
    if not os.path.isabs(sqlite_path):
        sqlite_path = str(BASE_DIR / sqlite_path)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
            "OPTIONS": {"timeout": 20},
        }
    }

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "users:profile"
LOGOUT_REDIRECT_URL = "core:home"

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT") or (BASE_DIR / "media"))

USE_S3 = env_bool("USE_S3", False)
if USE_S3:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "")
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "")
    AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", False)
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400, public"}
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }

# Rescue stale/invalid uploaded names instead of raising SuspiciousFileOperation.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

MAX_AUDIO_UPLOAD_SIZE = env_int("MAX_AUDIO_UPLOAD_SIZE", 80 * 1024 * 1024)
MAX_IMAGE_UPLOAD_SIZE = env_int("MAX_IMAGE_UPLOAD_SIZE", 8 * 1024 * 1024)

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "AVA Music <no-reply@avamusic.ir>")
CONTACT_NOTIFICATION_EMAIL = os.environ.get("CONTACT_NOTIFICATION_EMAIL", "")

# ---------------------------------------------------------------------------
# Cache / sessions
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ava-music",
        "TIMEOUT": 300,
    }
}
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # the player reads the CSRF token from the cookie
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7

# ---------------------------------------------------------------------------
# Security / production
# ---------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", True)

if env_bool("TRUST_PROXY_SSL_HEADER", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Application limits used by views/forms.
POSTS_PER_PAGE = env_int("POSTS_PER_PAGE", 12)
RELATED_SONGS_LIMIT = env_int("RELATED_SONGS_LIMIT", 4)
HOME_LATEST_LIMIT = env_int("HOME_LATEST_LIMIT", 6)

# Preserve the user's date/time choice between Gregorian storage and Jalali display.
SITE_DEFAULT_THEME = os.environ.get("SITE_DEFAULT_THEME", "dark")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

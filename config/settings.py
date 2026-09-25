"""Django settings for the German–Albanian learning application."""

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_ENVIRONMENT=(str, "development"),
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

ENVIRONMENT = env("DJANGO_ENVIRONMENT")
DEBUG = env("DJANGO_DEBUG")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if ENVIRONMENT == "development":
        SECRET_KEY = "django-insecure-development-only-change-me"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set outside development.")

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "courses",
    "learning",
    "speech",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "accounts.middleware.SingleActiveSessionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home"
AUTH_RATE_LIMIT_ATTEMPTS = env.int("AUTH_RATE_LIMIT_ATTEMPTS", default=10)
AUTH_RATE_LIMIT_WINDOW_SECONDS = env.int("AUTH_RATE_LIMIT_WINDOW_SECONDS", default=300)
SPEECH_MAX_RECORDING_SECONDS = env.int("SPEECH_MAX_RECORDING_SECONDS", default=15)
SPEECH_MAX_UPLOAD_BYTES = env.int("SPEECH_MAX_UPLOAD_BYTES", default=5 * 1024 * 1024)
SPEECH_WHISPER_MODEL = env("SPEECH_WHISPER_MODEL", default="base")
SPEECH_WHISPER_DEVICE = env("SPEECH_WHISPER_DEVICE", default="cpu")
SPEECH_WHISPER_COMPUTE_TYPE = env("SPEECH_WHISPER_COMPUTE_TYPE", default="int8")
SPEECH_TRANSCRIPTION_RATE_ATTEMPTS = env.int(
    "SPEECH_TRANSCRIPTION_RATE_ATTEMPTS", default=10
)
SPEECH_TRANSCRIPTION_RATE_WINDOW_SECONDS = env.int(
    "SPEECH_TRANSCRIPTION_RATE_WINDOW_SECONDS", default=300
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

MAILERS = {
    "default": {
        "BACKEND": env(
            "DJANGO_MAILER_BACKEND",
            default="django.core.mail.backends.console.EmailBackend",
        )
    }
}
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="Germanisht Shqip <noreply@example.com>",
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

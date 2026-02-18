from .base import *  # noqa
from .base import env, BASE_DIR
from urllib.parse import urlparse

DEBUG = True

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-local-key")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

FRONTEND_DOMAIN = urlparse(FRONTEND_URL).hostname or "localhost"

ALLOWED_HOSTS = list(
    {
        "localhost",
        "0.0.0.0",
        "127.0.0.1",
        "web",
        FRONTEND_DOMAIN,
    }
)

CORS_ALLOWED_ORIGINS = list(
    {
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        FRONTEND_URL,
    }
)

CSRF_TRUSTED_ORIGINS = list(
    {
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        FRONTEND_URL,
    }
)


# Local Database (Docker or Sqlite fallback)
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR}/db.sqlite3")
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# Cache (Redis)
CACHES = {"default": env.cache("REDIS_URL", default="locmemcache://")}

# Celery
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default=env("REDIS_URL", default="redis://localhost:6379/0")
)
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default=env("REDIS_URL", default="redis://localhost:6379/0"),
)

# Email - Output to console for local development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

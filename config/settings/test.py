from .base import *  # noqa
from .base import env, BASE_DIR

# SECURITY WARNING: keep the secret key used in production secret!
# Use a dummy key for testing. CI/Docker must inject this or rely on this default if base.py allows.
# However, since base.py might enforce env('DJANGO_SECRET_KEY'), we must ensure it's set in the env
# OR we override it here conceptually.
# NOTE: If base.py raises ImproperlyConfigured, this file won't even load.
# Implication: CI/Test environment MUST set DJANGO_SECRET_KEY to *something*, even if we override it here.
SECRET_KEY = "insecure-test-key-do-not-use-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database
# Use SQLite for tests to avoid PostgreSQL dependency issues in checking settings,
# OR strictly use the service defined in CI.
# For now, we prefer the CI configuration (Postgres) if available, or fall back to SQLite.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR}/db_test.sqlite3")
}

# Passwords
# Speed up tests by using a faster hasher
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Celery
CELERY_TASK_ALWAYS_EAGER = True

# Disable WhiteNoise storage for tests to avoid needing staticfiles
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

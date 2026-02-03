from .base import *

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY", default='django-insecure-local-key')
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# Local Database (Docker or Sqlite fallback)
DATABASES = {
    'default': env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR}/db.sqlite3")
}

# Cache (Redis)
CACHES = {
    "default": env.cache("REDIS_URL", default="locmemcache://")
}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")

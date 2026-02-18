import ssl

from .base import *  # noqa
from .base import env

# import dj_database_url # Removed to avoid extra dependency

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["onrender.com"])

# Ensure Sentry knows this is production
DJANGO_ENVIRONMENT = "production"
FRONTEND_URL = env("FRONTEND_URL")

# Database (Neon)
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["OPTIONS"] = {
    "sslmode": "require",
    "connect_timeout": 5,
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 5,
}


# Cache (Upstash Redis)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": ssl.CERT_REQUIRED},
        },
    }
}

# Celery (Upstash Redis)
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}

# Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy (Optional but recommended)
# CSP_DEFAULT_SRC = ("'self'",)

# CORS & CSRF
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[env("FRONTEND_URL")])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[env("FRONTEND_URL")])

# Render specific: Add Render URL to allowed hosts and trusted origins
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default=None)
if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    if f"https://{RENDER_EXTERNAL_HOSTNAME}" not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Email Configuration (Brevo)
# ------------------------------------------------------------------------------
# https://github.com/anymail/django-anymail/blob/main/docs/esps/brevo.md
EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
ANYMAIL = {
    "BREVO_API_KEY": env("BREVO_API_KEY"),
}

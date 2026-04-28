"""
Production settings for Bhutan NWFP Digital Marketplace & Management Platform.

Inherits from base.py and overlays security-hardened overrides:
  - DEBUG=False
  - Full HTTPS / HSTS enforcement
  - Secure cookies
  - Sentry error tracking (when SENTRY_DSN is set in the environment)
  - Optional cloud storage via django-storages
"""

from .base import *  # noqa: F401, F403
from .base import env, INSTALLED_APPS, MIDDLEWARE

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = False

# Production ALLOWED_HOSTS must be explicitly set via the ALLOWED_HOSTS
# environment variable — no safe fallback is appropriate here.
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# ---------------------------------------------------------------------------
# HTTPS / Security hardening
# ---------------------------------------------------------------------------
SECURE_HSTS_SECONDS = 31536000           # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ---------------------------------------------------------------------------
# Secure cookies
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 8        # 8 hours

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ---------------------------------------------------------------------------
# Email — configure via environment variables
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)

# ---------------------------------------------------------------------------
# Cache — Redis (set REDIS_URL in the environment)
# ---------------------------------------------------------------------------
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'nwfp',
        'TIMEOUT': 300,
    }
}

# ---------------------------------------------------------------------------
# Sentry error tracking (optional — only activated when SENTRY_DSN is set)
# ---------------------------------------------------------------------------
SENTRY_DSN = env('SENTRY_DSN', default='')

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    import logging

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
        send_default_pii=False,
        environment='production',
        release=env('APP_VERSION', default='unknown'),
    )

# ---------------------------------------------------------------------------
# Static / media storage — django-storages (S3-compatible)
# Activate by setting USE_S3=True and providing AWS_* variables.
# ---------------------------------------------------------------------------
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    INSTALLED_APPS = INSTALLED_APPS + ['storages']

    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='ap-southeast-1')
    AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com')
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_QUERYSTRING_AUTH = False

    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# ---------------------------------------------------------------------------
# Logging — structured output suitable for log aggregators
# ---------------------------------------------------------------------------
LOGGING['handlers']['console']['formatter'] = 'verbose'  # noqa: F405
LOGGING['root']['level'] = 'WARNING'                     # noqa: F405

# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------
# Disable the browsable API renderer in production for security and perf
REST_FRAMEWORK = {                                        # noqa: F405
    **globals().get('REST_FRAMEWORK', {}),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

CONN_MAX_AGE = env.int('CONN_MAX_AGE', default=60)
DATABASES['default']['CONN_MAX_AGE'] = CONN_MAX_AGE      # noqa: F405

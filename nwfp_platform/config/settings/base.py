"""
Base settings for Bhutan NWFP Digital Marketplace & Management Platform.

All environment-specific settings files (development.py, production.py)
inherit from this module via `from .base import *`.

Environment variables are read from a .env file (or the process environment)
using django-environ.  A .env.example file is provided in the project root.
"""

from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# BASE_DIR points to the project root (the directory that contains manage.py,
# config/, apps/, requirements/, etc.)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# django-environ initialisation
# ---------------------------------------------------------------------------
env = environ.Env(
    # Cast helpers — provide (type, default) tuples where useful
    DEBUG=(bool, False),
    USE_SPATIALITE=(bool, False),
)

# Read the .env file when present (silently ignored if absent so that
# production deployments can rely on real env vars instead)
environ.Env.read_env(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY')

# ALLOWED_HOSTS is always overridden by child settings but we supply a
# safe default so the base file is importable on its own.
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_gis',
    'django_filters',
    'django_htmx',
    'django_extensions',
    'whitenoise.runserver_nostatic',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.groups',
    'apps.products',
    'apps.inventory',
    'apps.marketplace',
    'apps.documents',
    'apps.spatial',
    'apps.approvals',
    'apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # APP_DIRS=True makes Django search for a `templates/` subdirectory
        # inside every installed application.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'apps.marketplace.context_processors.cart_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ---------------------------------------------------------------------------
# Database — PostGIS (overridden in development.py when USE_SPATIALITE=True)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgis://nwfp_user:nwfp_pass@localhost:5432/nwfp_db'),
}
# Ensure the PostGIS engine is used when a postgis:// URL is provided
DATABASES['default'].setdefault('ENGINE', 'django.contrib.gis.db.backends.postgis')

# ---------------------------------------------------------------------------
# Custom user model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Thimphu'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise compressed+hashed static files for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ---------------------------------------------------------------------------
# Media files
# ---------------------------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# ---------------------------------------------------------------------------
# Authentication redirects
# ---------------------------------------------------------------------------
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ---------------------------------------------------------------------------
# File upload limits
# ---------------------------------------------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB

# ---------------------------------------------------------------------------
# Email — overridden per environment
# ---------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = 'noreply@nwfp.bt'
SERVER_EMAIL = 'server@nwfp.bt'

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ---------------------------------------------------------------------------
# NWFP Platform-specific configuration
# ---------------------------------------------------------------------------
NWFP_CONFIG = {
    # Maximum file size users may upload via the platform UI (MB)
    'MAX_UPLOAD_SIZE_MB': 50,

    # Permitted upload file extensions (case-insensitive)
    'ALLOWED_FILE_TYPES': ['pdf', 'csv', 'geojson', 'zip', 'jpg', 'jpeg', 'png'],

    # Bhutan has 20 Dzongkhags (administrative districts)
    'DZONGKHAGS': 20,

    # NWFP product categories (Non-Wood Forest Products)
    'PRODUCT_CATEGORIES': [
        'medicinal_plants',
        'aromatic_plants',
        'edible_plants',
        'bamboo_cane',
        'resins_gums',
        'fungi_mushrooms',
        'fodder_plants',
        'dyes_tannins',
        'ornamental_plants',
        'other',
    ],

    # Unit types for inventory
    'UNIT_TYPES': ['kg', 'g', 'litre', 'ml', 'bundle', 'piece', 'bag', 'box'],
}

# ---------------------------------------------------------------------------
# django-extensions
# ---------------------------------------------------------------------------
SHELL_PLUS = 'ipython'
SHELL_PLUS_PRINT_SQL = True

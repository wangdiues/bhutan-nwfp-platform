"""
Local preview settings for machines without Docker/PostGIS/GDAL.

This is only for UI/workflow preview. Production and full GIS development
should use config.settings.development with PostGIS or SpatiaLite.
"""

import os

os.environ.setdefault('SECRET_KEY', 'local-preview-secret-key-not-for-production')

from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = env('SECRET_KEY', default='local-preview-secret-key-not-for-production')  # noqa: F405
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ROOT_URLCONF = 'config.urls_lite'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'nwfp_lite.sqlite3',  # noqa: F405
    }
}

INSTALLED_APPS = [
    app for app in INSTALLED_APPS  # noqa: F405
    if app not in {
        'django.contrib.gis',
        'rest_framework_gis',
        'apps.spatial',
        'apps.api',
    }
]

MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nwfp-local-lite-cache',
    }
}

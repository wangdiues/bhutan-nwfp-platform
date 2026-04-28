"""
Development settings for Bhutan NWFP Digital Marketplace & Management Platform.

Inherits from base.py and overlays developer-friendly overrides:
  - DEBUG=True
  - Console email backend
  - django-debug-toolbar
  - Optional SpatiaLite database (set USE_SPATIALITE=True in .env when
    a PostGIS instance is not available locally)
  - CORS allow-all for local frontend development
"""

from .base import *  # noqa: F401, F403
from .base import env, INSTALLED_APPS, MIDDLEWARE, DATABASES

# ---------------------------------------------------------------------------
# Core debug flag
# ---------------------------------------------------------------------------
DEBUG = True

# ---------------------------------------------------------------------------
# Allowed hosts — permissive for local development
# ---------------------------------------------------------------------------
ALLOWED_HOSTS = ['*']

# ---------------------------------------------------------------------------
# Database — swap to SpatiaLite when USE_SPATIALITE=True in .env
# ---------------------------------------------------------------------------
USE_SPATIALITE = env.bool('USE_SPATIALITE', default=False)

if USE_SPATIALITE:
    # SpatiaLite is a lightweight spatial SQLite extension, useful when
    # a PostGIS server is not available on the developer's machine.
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.spatialite',
            'NAME': BASE_DIR / 'nwfp_dev.sqlite3',  # noqa: F405
        }
    }
    # Path to the SpatiaLite module — adjust if your system places it
    # elsewhere (e.g. Homebrew on macOS: /opt/homebrew/lib/mod_spatialite.dylib)
    SPATIALITE_LIBRARY_PATH = env('SPATIALITE_LIBRARY_PATH', default='mod_spatialite')
else:
    # Use the PostGIS URL from .env (falls back to the base.py default)
    pass  # DATABASES already set correctly by base.py

# ---------------------------------------------------------------------------
# Installed apps — add debug toolbar
# ---------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + [
    'debug_toolbar',
    'corsheaders',
]

# ---------------------------------------------------------------------------
# Middleware — debug toolbar must come as early as possible; CORS after
# SecurityMiddleware
# ---------------------------------------------------------------------------
MIDDLEWARE = (
    ['debug_toolbar.middleware.DebugToolbarMiddleware']
    + ['corsheaders.middleware.CorsMiddleware']
    + list(MIDDLEWARE)
)

# ---------------------------------------------------------------------------
# django-debug-toolbar
# ---------------------------------------------------------------------------
INTERNAL_IPS = ['127.0.0.1', '::1']

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'SHOW_COLLAPSED': True,
}

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

# ---------------------------------------------------------------------------
# Email — print to console instead of sending
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ---------------------------------------------------------------------------
# CORS — allow all origins during local development
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Cache — simple in-memory cache (no Redis required locally)
# ---------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nwfp-dev-cache',
    }
}

# ---------------------------------------------------------------------------
# Static files — use the simpler storage in dev (no hashing)
# ---------------------------------------------------------------------------
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ---------------------------------------------------------------------------
# Logging — verbose output for the console in development
# ---------------------------------------------------------------------------
LOGGING['root']['level'] = 'DEBUG'  # noqa: F405
LOGGING['loggers']['django']['level'] = 'DEBUG'  # noqa: F405

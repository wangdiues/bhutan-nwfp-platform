"""
Root URL configuration for Bhutan NWFP Digital Marketplace & Management Platform.

URL structure
-------------
/                       -> marketplace (product listings, home page)
/accounts/              -> authentication, user profile, registration
/seller/                -> product management (CRUD for sellers)
/seller/inventory/      -> inventory management
/groups/                -> collector / seller group management
/management/            -> approval workflows (admin / officer views)
/documents/             -> document upload, download, management
/spatial/               -> map views, GIS data endpoints
/api/v1/                -> Django REST Framework API
/admin/                 -> Django admin site
/__debug__/             -> django-debug-toolbar (DEBUG mode only)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Bhutan NWFP Management'
admin.site.site_title = 'NWFP Admin Portal'
admin.site.index_title = 'Non-Wood Forest Products Administration'

urlpatterns = [
    # -----------------------------------------------------------------------
    # Django admin
    # -----------------------------------------------------------------------
    path('admin/', admin.site.urls),

    # -----------------------------------------------------------------------
    # Public-facing marketplace (home page lives here)
    # -----------------------------------------------------------------------
    path('', include('apps.marketplace.urls', namespace='marketplace')),

    # -----------------------------------------------------------------------
    # Authentication & user accounts
    # -----------------------------------------------------------------------
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # -----------------------------------------------------------------------
    # Seller tools — product and inventory management
    # -----------------------------------------------------------------------
    path('seller/', include('apps.products.urls', namespace='products')),
    path('seller/', include('apps.inventory.urls', namespace='inventory')),

    # -----------------------------------------------------------------------
    # Collector / seller group management
    # -----------------------------------------------------------------------
    path('groups/', include('apps.groups.urls', namespace='groups')),

    # -----------------------------------------------------------------------
    # Approval workflows (officers / administrators)
    # -----------------------------------------------------------------------
    path('management/', include('apps.approvals.urls', namespace='approvals')),

    # -----------------------------------------------------------------------
    # Document management
    # -----------------------------------------------------------------------
    path('documents/', include('apps.documents.urls', namespace='documents')),

    # -----------------------------------------------------------------------
    # Spatial / mapping views
    # -----------------------------------------------------------------------
    path('spatial/', include('apps.spatial.urls', namespace='spatial')),

    # -----------------------------------------------------------------------
    # REST API v1
    # -----------------------------------------------------------------------
    path('api/v1/', include('apps.api.urls', namespace='api')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ---------------------------------------------------------------------------
# Debug toolbar (development only)
# ---------------------------------------------------------------------------
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        # debug_toolbar not installed — this can happen if running development
        # settings without having installed requirements/development.txt yet.
        pass

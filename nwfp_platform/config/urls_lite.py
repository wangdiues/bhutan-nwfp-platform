from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView


admin.site.site_header = 'Bhutan NWFP Management'
admin.site.site_title = 'NWFP Admin Portal'
admin.site.index_title = 'Non-Wood Forest Products Administration'

spatial_lite_patterns = ([
    path('map/', TemplateView.as_view(template_name='spatial/map_unavailable.html'), name='map'),
], 'spatial')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.marketplace.urls', namespace='marketplace')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('seller/', include('apps.products.urls', namespace='products')),
    path('seller/', include('apps.inventory.urls', namespace='inventory')),
    path('groups/', include('apps.groups.urls', namespace='groups')),
    path('management/', include('apps.approvals.urls', namespace='approvals')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('spatial/', include(spatial_lite_patterns, namespace='spatial')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

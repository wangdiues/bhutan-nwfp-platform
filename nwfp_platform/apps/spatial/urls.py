from django.urls import path
from . import views

app_name = 'spatial'

urlpatterns = [
    path('map/', views.MapView.as_view(), name='map'),
    path('api/sites/', views.ResourceSiteGeoJSONView.as_view(), name='sites_geojson'),
    path('api/layers/', views.LayerListView.as_view(), name='layers'),
]

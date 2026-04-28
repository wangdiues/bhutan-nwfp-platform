from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from .models import ResourceSite, SpatialLayer


@admin.register(SpatialLayer)
class SpatialLayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'layer_type', 'is_public', 'created_at']
    list_filter = ['layer_type', 'is_public']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(ResourceSite)
class ResourceSiteAdmin(gis_admin.GISModelAdmin):
    list_display = ['name', 'group', 'site_type', 'species', 'status', 'dzongkhag']
    list_filter = ['site_type', 'status', 'dzongkhag']
    search_fields = ['name', 'species']
    readonly_fields = ['created_at']
    raw_id_fields = ['group', 'layer', 'created_by']
    fieldsets = (
        (None, {'fields': ('name', 'group', 'layer', 'site_type', 'status')}),
        ('Spatial', {'fields': ('geometry', 'dzongkhag', 'area_ha', 'elevation_m')}),
        ('Biology', {'fields': ('species',)}),
        ('Meta', {'fields': ('notes', 'source_file', 'created_by', 'created_at')}),
    )

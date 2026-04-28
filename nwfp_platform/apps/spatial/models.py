import uuid

from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.accounts.models import User

LAYER_TYPES = [
    ('group_boundary', 'Group Boundary'),
    ('resource_site', 'Resource Site'),
    ('harvest_zone', 'Harvest Zone'),
    ('protected_area', 'Protected Area'),
]

SITE_TYPES = [
    ('collection_site', 'Collection Site'),
    ('headquarters', 'Group Headquarters'),
    ('nursery', 'Nursery'),
    ('processing_site', 'Processing Site'),
]

SITE_STATUS = [
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('protected', 'Protected'),
]


class SpatialLayer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layer_type = models.CharField(max_length=30, choices=LAYER_TYPES, db_index=True)
    style_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='Leaflet style options JSON',
    )
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Spatial Layer'
        verbose_name_plural = 'Spatial Layers'
        ordering = ['name']

    def __str__(self):
        return self.name


class ResourceSite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    group = models.ForeignKey(
        'groups.NWFPGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resource_sites',
        db_index=True,
    )
    layer = models.ForeignKey(
        SpatialLayer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sites',
        db_index=True,
    )
    geometry = gis_models.GeometryField(srid=4326, help_text='Point or Polygon')
    site_type = models.CharField(max_length=30, choices=SITE_TYPES, db_index=True)
    species = models.CharField(max_length=200, blank=True, db_index=True)
    area_ha = models.FloatField(null=True, blank=True)
    elevation_m = models.FloatField(null=True, blank=True)
    dzongkhag = models.CharField(max_length=30, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=SITE_STATUS, default='active', db_index=True)
    notes = models.TextField(blank=True)
    source_file = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sites',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Resource Site'
        verbose_name_plural = 'Resource Sites'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.site_type})"

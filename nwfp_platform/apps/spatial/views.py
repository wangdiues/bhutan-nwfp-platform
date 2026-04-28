import json

from django.contrib.gis.serializers.geojson import Serializer as GeoJSONSerializer
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import DZONGKHAG_CHOICES

from .models import ResourceSite, SpatialLayer


class MapView(TemplateView):
    """
    Main map page showing public spatial layers with Leaflet.
    """

    template_name = 'spatial/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        public_layers = SpatialLayer.objects.filter(is_public=True).order_by('name')

        context.update(
            {
                'page_title': 'NWFP Resource Map',
                'layers': public_layers,
                'dzongkhags': DZONGKHAG_CHOICES,
            }
        )
        return context


class ResourceSiteGeoJSONView(View):
    """
    Returns a GeoJSON FeatureCollection of ResourceSite objects.

    Supported GET filters:
        dzongkhag   -- filter by dzongkhag code
        layer       -- filter by SpatialLayer pk
        status      -- filter by site status (active / inactive / protected)
    """

    def get(self, request):
        qs = ResourceSite.objects.select_related('group', 'layer').all()

        dzongkhag = request.GET.get('dzongkhag', '').strip()
        if dzongkhag:
            qs = qs.filter(dzongkhag=dzongkhag)

        layer_id = request.GET.get('layer', '').strip()
        if layer_id:
            qs = qs.filter(layer_id=layer_id)

        status = request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)

        # Use Django's built-in GeoJSON serializer.
        serializer = GeoJSONSerializer()
        geojson_str = serializer.serialize(
            qs,
            geometry_field='geometry',
            srid=4326,
            fields=['id', 'name', 'site_type', 'species', 'dzongkhag', 'status', 'notes'],
            use_natural_foreign_keys=False,
        )

        return HttpResponse(geojson_str, content_type='application/geo+json')


class LayerListView(View):
    """
    Returns a JSON array of public SpatialLayer objects for map legend / control.
    """

    def get(self, request):
        layers = SpatialLayer.objects.filter(is_public=True).values(
            'id',
            'name',
            'description',
            'layer_type',
            'style_config',
        )
        return JsonResponse(list(layers), safe=False)

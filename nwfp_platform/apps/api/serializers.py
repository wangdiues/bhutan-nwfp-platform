from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.groups.models import NWFPGroup
from apps.inventory.models import HarvestBatch
from apps.marketplace.models import Order, OrderItem
from apps.products.models import Product
from apps.spatial.models import ResourceSite


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


class GroupSerializer(serializers.ModelSerializer):
    """
    Concise read-only representation of an NWFPGroup for embedding and listing.
    """

    class Meta:
        model = NWFPGroup
        fields = [
            'id',
            'name',
            'slug',
            'dzongkhag',
            'status',
            'total_members',
            'contact_email',
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class _NestedGroupSerializer(serializers.ModelSerializer):
    """Minimal group info nested inside a product."""

    class Meta:
        model = NWFPGroup
        fields = ['id', 'name', 'dzongkhag']


class ProductSerializer(serializers.ModelSerializer):
    """
    Full read-only product representation, including a nested group summary
    and a resolved URL for the primary product image.
    """

    group = _NestedGroupSerializer(read_only=True)
    primary_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'group',
            'category',
            'scientific_name',
            'description',
            'price',
            'unit',
            'status',
            'harvest_season',
            'primary_image_url',
        ]
        read_only_fields = fields

    def get_primary_image_url(self, obj):
        """Return the absolute URL of the primary image, or None."""
        primary_image = obj.primary_image
        if primary_image and primary_image.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Read-only line-item representation nested inside an Order.
    """

    class Meta:
        model = OrderItem
        fields = [
            'product_name',
            'batch_code',
            'quantity',
            'unit_price',
            'subtotal',
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """
    Order with nested line items.  Write operations restricted to
    buyer-owned orders via the viewset queryset.
    """

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'total_amount',
            'placed_at',
            'buyer_name',
            'buyer_email',
            'buyer_phone',
            'buyer_address',
            'notes',
            'items',
        ]
        read_only_fields = [
            'id',
            'order_number',
            'placed_at',
            'items',
        ]


# ---------------------------------------------------------------------------
# Harvest batches
# ---------------------------------------------------------------------------


class HarvestBatchSerializer(serializers.ModelSerializer):
    """
    Full serializer for HarvestBatch — used by officers and admins.
    """

    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = HarvestBatch
        fields = [
            'id',
            'group',
            'group_name',
            'species',
            'scientific_name',
            'harvest_date',
            'quantity_harvested',
            'quantity_unit',
            'site_name',
            'latitude',
            'longitude',
            'elevation_m',
            'collector_count',
            'notes',
            'officer_verified',
            'officer',
            'uploaded_via_csv',
            'source_file',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'group_name']


# ---------------------------------------------------------------------------
# Spatial / GIS
# ---------------------------------------------------------------------------


class ResourceSiteSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON feature serializer for ResourceSite objects.
    Geometry is exposed as GeoJSON; group name is denormalised for convenience.
    """

    group_name = serializers.CharField(source='group.name', read_only=True, default='')

    class Meta:
        model = ResourceSite
        geo_field = 'geometry'
        fields = [
            'id',
            'name',
            'group_name',
            'site_type',
            'species',
            'dzongkhag',
            'status',
            'area_ha',
            'elevation_m',
            'notes',
        ]
        id_field = 'id'

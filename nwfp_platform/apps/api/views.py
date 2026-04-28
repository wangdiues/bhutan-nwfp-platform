from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.groups.models import NWFPGroup
from apps.inventory.models import HarvestBatch
from apps.marketplace.models import Order
from apps.products.models import Product
from apps.spatial.models import ResourceSite

from .serializers import (
    GroupSerializer,
    HarvestBatchSerializer,
    OrderSerializer,
    ProductSerializer,
    ResourceSiteSerializer,
)


# ---------------------------------------------------------------------------
# Custom permissions
# ---------------------------------------------------------------------------


class IsOfficerOrAdmin(permissions.BasePermission):
    """
    Grants access only to users with role 'officer' or 'admin'.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('officer', 'admin')
        )


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for published, non-deleted products.

    Supports filtering by ``category`` and ``group__dzongkhag``, and
    full-text search on ``name`` and ``scientific_name``.
    """

    serializer_class = ProductSerializer
    queryset = (
        Product.objects.filter(status='published', is_deleted=False)
        .select_related('group', 'category')
        .prefetch_related('images')
        .order_by('-created_at')
    )

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'group__dzongkhag']
    search_fields = ['name', 'scientific_name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for active, non-deleted NWFP groups.
    """

    serializer_class = GroupSerializer
    queryset = (
        NWFPGroup.objects.filter(status='active', is_deleted=False)
        .order_by('name')
    )

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dzongkhag', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'total_members']
    ordering = ['name']


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Orders.  Requires authentication; users only see their own orders.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['placed_at', 'total_amount']
    ordering = ['-placed_at']

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .prefetch_related('items')
            .order_by('-placed_at')
        )

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)


class HarvestBatchViewSet(viewsets.ModelViewSet):
    """
    CRUD API for HarvestBatch records.
    Restricted to users with role 'officer' or 'admin'.
    """

    serializer_class = HarvestBatchSerializer
    permission_classes = [IsOfficerOrAdmin]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'officer_verified', 'quantity_unit']
    search_fields = ['species', 'scientific_name', 'site_name']
    ordering_fields = ['harvest_date', 'created_at', 'species']
    ordering = ['-harvest_date']

    def get_queryset(self):
        return HarvestBatch.objects.select_related('group', 'officer').order_by(
            '-harvest_date'
        )

    def perform_create(self, serializer):
        serializer.save(officer=self.request.user)


class ResourceSiteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only GeoJSON API for ResourceSite objects.

    Supports filtering by ``dzongkhag``, ``site_type`` and ``species``.
    """

    serializer_class = ResourceSiteSerializer
    queryset = (
        ResourceSite.objects.filter(status='active')
        .select_related('group', 'layer')
        .order_by('name')
    )

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['dzongkhag', 'site_type', 'species']
    search_fields = ['name', 'species', 'notes']

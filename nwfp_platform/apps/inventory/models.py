import uuid

from django.db import models

from apps.accounts.models import User
from apps.groups.models import NWFPGroup
from apps.products.models import Product

BATCH_STATUS = [
    ('available', 'Available'),
    ('low_stock', 'Low Stock'),
    ('out_of_stock', 'Out of Stock'),
    ('expired', 'Expired'),
    ('reserved', 'Reserved'),
]


class InventoryBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='batches',
        db_index=True,
    )
    batch_code = models.CharField(max_length=50, unique=True, db_index=True)
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_reserved = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    harvest_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    harvest_location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=BATCH_STATUS, default='available', db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inventory Batch'
        verbose_name_plural = 'Inventory Batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_code} ({self.product.name})"

    @property
    def quantity_net(self):
        return self.quantity_available - self.quantity_reserved


class HarvestBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        NWFPGroup,
        on_delete=models.CASCADE,
        related_name='harvest_batches',
        db_index=True,
    )
    species = models.CharField(max_length=200, db_index=True)
    scientific_name = models.CharField(max_length=200, blank=True)
    harvest_date = models.DateField()
    quantity_harvested = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_unit = models.CharField(max_length=20)
    site_name = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    elevation_m = models.FloatField(null=True, blank=True)
    collector_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    officer_verified = models.BooleanField(default=False)
    officer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_harvests',
        db_index=True,
    )
    uploaded_via_csv = models.BooleanField(default=False)
    source_file = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Harvest Batch'
        verbose_name_plural = 'Harvest Batches'
        ordering = ['-harvest_date']

    def __str__(self):
        return f"{self.species} - {self.group.name} ({self.harvest_date})"

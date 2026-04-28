from django.contrib import admin

from .models import HarvestBatch, InventoryBatch


@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'product', 'quantity_available', 'status', 'harvest_date']
    list_filter = ['status', 'product__group__dzongkhag']
    search_fields = ['batch_code', 'product__name']
    readonly_fields = ['created_at']
    raw_id_fields = ['product']
    fieldsets = (
        (None, {'fields': ('product', 'batch_code', 'status')}),
        ('Quantities', {'fields': ('quantity_available', 'quantity_reserved', 'unit_price')}),
        ('Harvest Info', {'fields': ('harvest_date', 'expiry_date', 'harvest_location')}),
        ('Notes', {'fields': ('notes', 'created_at')}),
    )


@admin.register(HarvestBatch)
class HarvestBatchAdmin(admin.ModelAdmin):
    list_display = ['species', 'group', 'harvest_date', 'quantity_harvested', 'officer_verified']
    list_filter = ['officer_verified', 'group__dzongkhag', 'uploaded_via_csv']
    search_fields = ['species', 'scientific_name', 'group__name', 'site_name']
    readonly_fields = ['created_at']
    raw_id_fields = ['group', 'officer']
    fieldsets = (
        (None, {'fields': ('group', 'species', 'scientific_name', 'harvest_date')}),
        ('Quantity', {'fields': ('quantity_harvested', 'quantity_unit')}),
        ('Location', {'fields': ('site_name', 'latitude', 'longitude', 'elevation_m')}),
        ('Verification', {'fields': ('officer_verified', 'officer', 'collector_count', 'notes')}),
        ('Source', {'fields': ('uploaded_via_csv', 'source_file', 'created_at')}),
    )

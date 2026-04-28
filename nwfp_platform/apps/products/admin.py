from django.contrib import admin

from .models import Product, ProductCategory, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'order']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'order']
    list_filter = ['parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'category', 'status', 'price', 'unit']
    list_filter = ['status', 'category', 'group__dzongkhag']
    search_fields = ['name', 'scientific_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'view_count']
    raw_id_fields = ['group', 'category', 'created_by']
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'group', 'category', 'status')}),
        ('Details', {'fields': ('scientific_name', 'description', 'price', 'unit', 'harvest_season', 'certifications')}),
        ('Meta', {'fields': ('created_by', 'view_count', 'is_deleted', 'created_at', 'updated_at')}),
    )

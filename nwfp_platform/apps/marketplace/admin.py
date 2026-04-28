from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem, Shipment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product_name', 'batch_code', 'quantity', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']


class ShipmentInline(admin.StackedInline):
    model = Shipment
    extra = 0
    fields = ['tracking_number', 'carrier', 'dispatched_at', 'estimated_delivery', 'delivered_at', 'notes']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['batch', 'quantity', 'added_at']
    readonly_fields = ['added_at']
    raw_id_fields = ['batch']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer_name', 'status', 'total_amount', 'placed_at']
    list_filter = ['status']
    search_fields = ['order_number', 'buyer_email', 'buyer_name']
    readonly_fields = ['order_number', 'placed_at', 'updated_at']
    raw_id_fields = ['buyer']
    inlines = [OrderItemInline, ShipmentInline]
    fieldsets = (
        (None, {'fields': ('order_number', 'status', 'total_amount', 'notes')}),
        ('Buyer', {'fields': ('buyer', 'buyer_name', 'buyer_email', 'buyer_phone', 'buyer_address')}),
        ('Timestamps', {'fields': ('placed_at', 'updated_at')}),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']
    inlines = [CartItemInline]


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_number', 'carrier', 'dispatched_at', 'delivered_at']
    list_filter = ['carrier']
    search_fields = ['tracking_number', 'order__order_number']
    raw_id_fields = ['order']

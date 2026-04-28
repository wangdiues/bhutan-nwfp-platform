from django.contrib import admin

from .models import ApprovalRequest, AuditLog, Notification


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['object_repr', 'request_type', 'status', 'requested_by', 'requested_at']
    list_filter = ['status', 'request_type']
    search_fields = ['object_repr']
    readonly_fields = ['requested_at', 'decided_at', 'content_type', 'object_id']
    raw_id_fields = ['requested_by', 'assigned_to']
    fieldsets = (
        (None, {'fields': ('request_type', 'status', 'object_repr', 'content_type', 'object_id')}),
        ('Assignment', {'fields': ('requested_by', 'assigned_to')}),
        ('Notes', {'fields': ('notes', 'decision_notes')}),
        ('Timestamps', {'fields': ('requested_at', 'decided_at')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'object_repr', 'ip_address', 'timestamp']
    list_filter = ['action']
    search_fields = ['object_repr', 'user__email']
    readonly_fields = [
        'id', 'user', 'action', 'content_type', 'object_id',
        'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['title', 'recipient__email']
    readonly_fields = ['created_at']
    raw_id_fields = ['recipient']

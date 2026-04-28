from django.contrib import admin

from .models import GroupMember, GroupStatusHistory, NWFPGroup


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    fields = ['user', 'role', 'joined_date', 'is_active']
    readonly_fields = ['joined_date']
    raw_id_fields = ['user']


class GroupStatusHistoryInline(admin.TabularInline):
    model = GroupStatusHistory
    extra = 0
    fields = ['old_status', 'new_status', 'changed_by', 'reason', 'changed_at']
    readonly_fields = ['changed_at']
    raw_id_fields = ['changed_by']


@admin.register(NWFPGroup)
class NWFPGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'dzongkhag', 'status', 'total_members', 'created_at']
    list_filter = ['status', 'dzongkhag']
    search_fields = ['name', 'registration_number']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['created_by']
    inlines = [GroupMemberInline, GroupStatusHistoryInline]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'registration_number', 'status', 'description')}),
        ('Location', {'fields': ('dzongkhag', 'gewog', 'village', 'headquarters_lat', 'headquarters_lon')}),
        ('Contact', {'fields': ('contact_email', 'contact_phone')}),
        ('Details', {'fields': ('established_date', 'total_members', 'created_by', 'dissolved_at', 'is_deleted')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'is_active', 'group__dzongkhag']
    search_fields = ['user__email', 'user__full_name', 'group__name']
    raw_id_fields = ['group', 'user']

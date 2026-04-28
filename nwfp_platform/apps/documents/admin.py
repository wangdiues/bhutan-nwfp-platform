from django.contrib import admin

from .models import Certificate, Document


class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 0
    fields = ['certificate_type', 'issued_by', 'certificate_number', 'issue_date', 'expiry_date', 'is_valid']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'group', 'status', 'created_at']
    list_filter = ['file_type', 'status']
    search_fields = ['title']
    readonly_fields = ['created_at', 'file_size']
    raw_id_fields = ['group', 'product', 'uploaded_by']
    inlines = [CertificateInline]
    fieldsets = (
        (None, {'fields': ('title', 'file', 'file_type', 'file_size', 'status')}),
        ('Relations', {'fields': ('group', 'product', 'uploaded_by')}),
        ('Content', {'fields': ('description', 'extracted_text')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'certificate_type', 'issued_by', 'issue_date', 'expiry_date', 'is_valid']
    list_filter = ['certificate_type', 'is_valid']
    search_fields = ['certificate_number', 'issued_by']
    raw_id_fields = ['document']

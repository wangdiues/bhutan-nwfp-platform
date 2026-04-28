import os
import uuid

from django.db import models

from apps.accounts.models import User

FILE_TYPES = [
    ('pdf', 'PDF'),
    ('csv', 'CSV'),
    ('geojson', 'GeoJSON'),
    ('shapefile', 'Shapefile'),
    ('image', 'Image'),
    ('other', 'Other'),
]

DOC_STATUS = [
    ('pending', 'Pending Processing'),
    ('processed', 'Processed'),
    ('failed', 'Processing Failed'),
]


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, db_index=True)
    file_size = models.PositiveIntegerField(default=0, help_text='Size in bytes')
    group = models.ForeignKey(
        'groups.NWFPGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        db_index=True,
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        db_index=True,
    )
    description = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True, help_text='Text extracted from PDF')
    status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class Certificate(models.Model):
    CERT_TYPES = [
        ('management_plan', 'Management Plan'),
        ('harvest_permit', 'Harvest Permit'),
        ('quality_cert', 'Quality Certificate'),
        ('organic', 'Organic Certification'),
        ('other', 'Other'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='certificates',
        db_index=True,
    )
    certificate_type = models.CharField(max_length=30, choices=CERT_TYPES, db_index=True)
    issued_by = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.certificate_type} - {self.certificate_number}"

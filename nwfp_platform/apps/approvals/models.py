import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.accounts.models import User

REQUEST_TYPES = [
    ('product_approval', 'Product Approval'),
    ('group_registration', 'Group Registration'),
    ('document_validation', 'Document Validation'),
    ('seller_verification', 'Seller Verification'),
]

REQUEST_STATUS = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]

AUDIT_ACTIONS = [
    ('create', 'Create'),
    ('update', 'Update'),
    ('delete', 'Delete'),
    ('login', 'Login'),
    ('logout', 'Logout'),
    ('approve', 'Approve'),
    ('reject', 'Reject'),
    ('upload', 'Upload'),
]

NOTIF_TYPES = [
    ('approval_needed', 'Approval Needed'),
    ('approval_done', 'Approval Done'),
    ('order_update', 'Order Update'),
    ('system', 'System'),
]


class ApprovalRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True,
    )
    object_id = models.CharField(max_length=50)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=200)
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES, db_index=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending', db_index=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_approvals',
        db_index=True,
    )
    notes = models.TextField(blank=True)
    decision_notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Approval Request'
        verbose_name_plural = 'Approval Requests'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.request_type}: {self.object_repr} ({self.status})"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True,
    )
    action = models.CharField(max_length=20, choices=AUDIT_ACTIONS, db_index=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIF_TYPES, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    related_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"

import uuid

from django.db import models
from django.utils.text import slugify

from apps.accounts.models import DZONGKHAG_CHOICES, User

GROUP_STATUS = [
    ('pending', 'Pending'),
    ('active', 'Active'),
    ('suspended', 'Suspended'),
    ('dissolved', 'Dissolved'),
]


class NWFPGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    registration_number = models.CharField(max_length=50, unique=True, blank=True)
    dzongkhag = models.CharField(max_length=30, choices=DZONGKHAG_CHOICES, db_index=True)
    gewog = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)
    established_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=GROUP_STATUS, default='pending', db_index=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    headquarters_lat = models.FloatField(null=True, blank=True)
    headquarters_lon = models.FloatField(null=True, blank=True)
    total_members = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dissolved_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'NWFP Group'
        verbose_name_plural = 'NWFP Groups'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class GroupMember(models.Model):
    MEMBER_ROLES = [
        ('chairperson', 'Chairperson'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
    ]

    group = models.ForeignKey(
        NWFPGroup,
        on_delete=models.CASCADE,
        related_name='members',
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        db_index=True,
    )
    role = models.CharField(max_length=20, choices=MEMBER_ROLES, default='member')
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Group Member'
        verbose_name_plural = 'Group Members'
        unique_together = [('group', 'user')]
        ordering = ['role', 'user__full_name']

    def __str__(self):
        return f"{self.user.full_name} - {self.group.name} ({self.role})"


class GroupStatusHistory(models.Model):
    group = models.ForeignKey(
        NWFPGroup,
        on_delete=models.CASCADE,
        related_name='status_history',
        db_index=True,
    )
    old_status = models.CharField(max_length=20, choices=GROUP_STATUS)
    new_status = models.CharField(max_length=20, choices=GROUP_STATUS)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        db_index=True,
    )
    reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Group Status History'
        verbose_name_plural = 'Group Status Histories'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.group.name}: {self.old_status} -> {self.new_status}"

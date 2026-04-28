import uuid

from django.db import models
from django.utils.text import slugify

from apps.accounts.models import User
from apps.groups.models import NWFPGroup

PRODUCT_STATUS = [
    ('draft', 'Draft'),
    ('review', 'Under Review'),
    ('approved', 'Approved'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]

UNIT_CHOICES = [
    ('kg', 'Kilogram'),
    ('g', 'Gram'),
    ('bundle', 'Bundle'),
    ('piece', 'Piece'),
    ('liter', 'Liter'),
    ('pack', 'Pack'),
]


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Icon name or emoji')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        db_index=True,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    group = models.ForeignKey(
        NWFPGroup,
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True,
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        db_index=True,
    )
    scientific_name = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    status = models.CharField(max_length=20, choices=PRODUCT_STATUS, default='draft', db_index=True)
    harvest_season = models.CharField(max_length=100, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.group.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.group.name}")
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        db_index=True,
    )
    image = models.ImageField(upload_to='products/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

DZONGKHAG_CHOICES = [
    ('bumthang', 'Bumthang'),
    ('chhukha', 'Chhukha'),
    ('dagana', 'Dagana'),
    ('gasa', 'Gasa'),
    ('haa', 'Haa'),
    ('lhuentse', 'Lhuentse'),
    ('mongar', 'Mongar'),
    ('paro', 'Paro'),
    ('pemagatshel', 'Pemagatshel'),
    ('punakha', 'Punakha'),
    ('samdrup_jongkhar', 'Samdrup Jongkhar'),
    ('samtse', 'Samtse'),
    ('sarpang', 'Sarpang'),
    ('thimphu', 'Thimphu'),
    ('trashigang', 'Trashigang'),
    ('trashi_yangtse', 'Trashi Yangtse'),
    ('trongsa', 'Trongsa'),
    ('tsirang', 'Tsirang'),
    ('wangdue', 'Wangdue Phodrang'),
    ('zhemgang', 'Zhemgang'),
]


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('public', 'Public Customer'),
        ('seller', 'Seller'),
        ('officer', 'Dzongkhag Officer'),
        ('admin', 'National Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='public', db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    dzongkhag = models.CharField(max_length=30, choices=DZONGKHAG_CHOICES, blank=True, db_index=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def is_seller(self):
        return self.role == 'seller'

    @property
    def is_officer(self):
        return self.role == 'officer'

    @property
    def is_admin_user(self):
        return self.role == 'admin'


class SellerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='seller_profile',
    )
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verifications',
    )

    class Meta:
        verbose_name = 'Seller Profile'
        verbose_name_plural = 'Seller Profiles'

    def __str__(self):
        return f"Seller: {self.user.full_name}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    dzongkhag = models.CharField(max_length=30, choices=DZONGKHAG_CHOICES, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'

    def __str__(self):
        return f"Customer: {self.user.full_name}"

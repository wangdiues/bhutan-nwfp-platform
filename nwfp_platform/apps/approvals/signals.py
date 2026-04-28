from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.approvals.models import ApprovalRequest, Notification
from apps.groups.models import NWFPGroup
from apps.products.models import Product

try:
    from apps.marketplace.models import Order
except ImportError:
    from apps.orders.models import Order


def _old_status(sender, instance):
    if not instance.pk:
        return None
    try:
        return sender.objects.only('status').get(pk=instance.pk).status
    except sender.DoesNotExist:
        return None


def _request_user(instance):
    user = getattr(instance, 'created_by', None)
    if user:
        return user

    group = getattr(instance, 'group', None)
    user = getattr(group, 'created_by', None)
    if user:
        return user

    User = get_user_model()
    return User.objects.filter(is_active=True, role__in=['officer', 'admin']).order_by('role').first()


def _create_approval_request(instance, request_type):
    requested_by = _request_user(instance)
    if requested_by is None:
        return

    content_type = ContentType.objects.get_for_model(instance, for_concrete_model=False)
    ApprovalRequest.objects.get_or_create(
        content_type=content_type,
        object_id=str(instance.pk),
        request_type=request_type,
        status='pending',
        defaults={
            'object_repr': str(instance)[:200],
            'requested_by': requested_by,
        },
    )


@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=NWFPGroup)
@receiver(pre_save, sender=Order)
def remember_previous_status(sender, instance, **kwargs):
    instance._previous_status = _old_status(sender, instance)


@receiver(post_save, sender=Product)
def create_product_approval_request(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_status', None)
    if instance.status == 'review' and (created or previous != instance.status):
        _create_approval_request(instance, 'product_approval')


@receiver(post_save, sender=NWFPGroup)
def create_group_approval_request(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_status', None)
    if instance.status == 'pending' and (created or previous != instance.status):
        _create_approval_request(instance, 'group_registration')


@receiver(post_save, sender=Order)
def create_order_status_notification(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_status', None)
    if created or instance.status not in {'confirmed', 'dispatched'} or previous == instance.status:
        return
    if not instance.buyer:
        return

    status_label = instance.get_status_display() if hasattr(instance, 'get_status_display') else instance.status.title()
    Notification.objects.create(
        recipient=instance.buyer,
        title=f'Order {status_label}',
        message=f'Your order {instance.order_number} is now {status_label.lower()}.',
        notification_type='order_update',
        related_url=f'/orders/{instance.order_number}/',
    )

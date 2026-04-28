from decimal import Decimal


def cart_processor(request):
    return {'cart_count': _cart_count(request)}


def _cart_count(request):
    try:
        from django.db.models import Sum
        from apps.marketplace.models import Cart

        cart = _current_cart(request, Cart)
        if cart is None:
            return 0

        total = cart.items.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        return int(total) if total == total.to_integral_value() else float(total)
    except Exception:
        return 0


def _current_cart(request, Cart):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return Cart.objects.filter(user=user).order_by('-updated_at').first()

    session_key = getattr(request.session, 'session_key', None)
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key).order_by('-updated_at').first()

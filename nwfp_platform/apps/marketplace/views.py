import json
import logging
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.groups.models import NWFPGroup
from apps.inventory.models import InventoryBatch
from apps.products.models import Product, ProductCategory

from .models import Cart, CartItem, Order, OrderItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _get_or_create_cart(request):
    """
    Return (cart, created).

    For authenticated users the cart is tied to the user.
    For anonymous users the cart is tied to the session key.
    """
    if not request.session.session_key:
        request.session.create()

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'session_key': request.session.session_key},
        )
    else:
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None,
        )
    return cart, created


# ---------------------------------------------------------------------------
# Public marketplace views
# ---------------------------------------------------------------------------


class MarketplaceHomeView(TemplateView):
    """
    Public home page: featured products, category list, summary statistics.
    """

    template_name = 'marketplace/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        featured_products = (
            Product.objects.filter(status='published', is_deleted=False)
            .select_related('group', 'category')
            .prefetch_related('images')
            .order_by('-created_at')[:8]
        )

        categories = ProductCategory.objects.all().order_by('order', 'name')

        context.update(
            {
                'page_title': 'Bhutan NWFP Digital Marketplace',
                'featured_products': featured_products,
                'categories': categories,
                'groups_count': NWFPGroup.objects.filter(
                    is_deleted=False, status='active'
                ).count(),
                'products_count': Product.objects.filter(
                    status='published', is_deleted=False
                ).count(),
            }
        )
        return context


class ProductCatalogueView(ListView):
    """
    Searchable, filterable public product catalogue.

    Supported GET params: q, category, dzongkhag, price_min, price_max
    """

    template_name = 'marketplace/catalogue.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Product.objects.filter(status='published', is_deleted=False)
            .select_related('group', 'category')
            .prefetch_related('images')
            .order_by('-created_at')
        )

        params = self.request.GET

        # Full-text search across name and description.
        q = params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

        # Filter by category slug.
        category = params.get('category', '').strip()
        if category:
            qs = qs.filter(category__slug=category)

        # Filter by group's dzongkhag.
        dzongkhag = params.get('dzongkhag', '').strip()
        if dzongkhag:
            qs = qs.filter(group__dzongkhag=dzongkhag)

        # Price range filters.
        price_min = params.get('price_min', '').strip()
        price_max = params.get('price_max', '').strip()
        if price_min:
            try:
                qs = qs.filter(price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                qs = qs.filter(price__lte=float(price_max))
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Browse Products'
        context['categories'] = ProductCategory.objects.all().order_by('order', 'name')
        context['search_params'] = self.request.GET
        return context


class ProductDetailPublicView(DetailView):
    """
    Public product detail page.  Increments view_count on each visit.
    """

    template_name = 'marketplace/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            Product.objects.filter(status='published', is_deleted=False)
            .select_related('group', 'category')
            .prefetch_related('images')
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count atomically to avoid lost updates under concurrency.
        Product.objects.filter(pk=obj.pk).update(view_count=obj.view_count + 1)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['page_title'] = product.name
        context['related_products'] = (
            Product.objects.filter(
                category=product.category,
                status='published',
                is_deleted=False,
            )
            .exclude(pk=product.pk)
            .select_related('group')
            .prefetch_related('images')[:4]
        )
        # Available inventory batches for add-to-cart.
        context['batches'] = InventoryBatch.objects.filter(
            product=product,
            status='available',
        ).order_by('-harvest_date')
        return context


# ---------------------------------------------------------------------------
# Cart views
# ---------------------------------------------------------------------------


class CartView(TemplateView):
    """
    Display the current cart contents.
    """

    template_name = 'marketplace/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, _ = _get_or_create_cart(self.request)
        items = cart.items.select_related(
            'batch__product__group', 'batch__product__category'
        ).all()
        context.update(
            {
                'page_title': 'Your Cart',
                'cart': cart,
                'cart_items': items,
                'cart_total': cart.total,
            }
        )
        return context


class CartAddView(View):
    """
    POST: Add an InventoryBatch item to the cart.

        Accepts JSON body or form-encoded data:
        batch_id  (UUID, required)
        quantity  (Decimal/float, optional, default 1)

    Returns JSON so it can be used from HTMX / fetch() without a full page reload.
    """

    http_method_names = ['post']

    def post(self, request):
        # Support both JSON bodies (HTMX/fetch) and classic form posts.
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = json.loads(request.body)
            except (ValueError, KeyError):
                return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        else:
            body = request.POST

        batch_id = body.get('batch_id')
        quantity = body.get('quantity', 1)

        if not batch_id:
            return JsonResponse({'error': 'batch_id is required.'}, status=400)

        try:
            quantity = Decimal(str(quantity))
            if quantity <= 0:
                raise ValueError
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({'error': 'quantity must be a positive number.'}, status=400)

        batch = get_object_or_404(InventoryBatch, pk=batch_id, status='available')
        if quantity > batch.quantity_net:
            return JsonResponse(
                {'error': f'Only {batch.quantity_net} {batch.product.unit} available.'},
                status=400,
            )

        cart, _ = _get_or_create_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            batch=batch,
            defaults={'quantity': quantity},
        )
        if not created:
            requested_quantity = cart_item.quantity + quantity
            if requested_quantity > batch.quantity_net:
                return JsonResponse(
                    {'error': f'Only {batch.quantity_net} {batch.product.unit} available.'},
                    status=400,
                )
            cart_item.quantity = requested_quantity
            cart_item.save(update_fields=['quantity'])

        cart_count = cart.items.count()

        # For HTMX requests, a lightweight JSON response suffices.
        return JsonResponse(
            {
                'success': True,
                'product_name': batch.product.name,
                'cart_count': cart_count,
                'created': created,
            }
        )


class CartRemoveView(View):
    """
    POST: Remove a CartItem by its pk.
    """

    http_method_names = ['post']

    def post(self, request, item_id):
        cart, _ = _get_or_create_cart(request)
        CartItem.objects.filter(pk=item_id, cart=cart).delete()

        if request.htmx if hasattr(request, 'htmx') else False:
            # Return the updated cart fragment for HTMX out-of-band swap.
            from django.template.loader import render_to_string
            items = cart.items.select_related('batch__product').all()
            html = render_to_string(
                'marketplace/partials/cart_items.html',
                {'cart': cart, 'cart_items': items},
                request=request,
            )
            return JsonResponse({'html': html})

        return redirect('marketplace:cart')


# ---------------------------------------------------------------------------
# Checkout & order views
# ---------------------------------------------------------------------------


class CheckoutView(View):
    """
    GET: Render the checkout form.
    POST: Create an Order from the current cart and clear the cart.
    """

    template_name = 'marketplace/checkout.html'

    def get(self, request):
        from django.shortcuts import render
        cart, _ = _get_or_create_cart(request)
        items = cart.items.select_related('batch__product').all()
        if not items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('marketplace:cart')
        return render(
            request,
            self.template_name,
            {
                'page_title': 'Checkout',
                'cart': cart,
                'cart_items': items,
                'cart_total': cart.total,
            },
        )

    @transaction.atomic
    def post(self, request):
        cart, _ = _get_or_create_cart(request)
        items = cart.items.select_related('batch__product').all()

        if not items.exists():
            messages.error(request, 'Cannot place an empty order.')
            return redirect('marketplace:cart')

        # Collect buyer information from POST data.
        buyer_name = request.POST.get('buyer_name', '').strip()
        buyer_email = request.POST.get('buyer_email', '').strip()
        buyer_phone = request.POST.get('buyer_phone', '').strip()
        buyer_address = request.POST.get('buyer_address', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not buyer_name or not buyer_email or not buyer_address:
            messages.error(request, 'Please fill in all required fields.')
            from django.shortcuts import render
            return render(
                request,
                self.template_name,
                {
                    'page_title': 'Checkout',
                    'cart': cart,
                    'cart_items': items,
                    'cart_total': cart.total,
                    'error': 'Name, email and address are required.',
                },
            )

        # Compute total from cart items.
        total_amount = cart.total

        for item in items:
            if item.quantity > item.batch.quantity_net:
                messages.error(
                    request,
                    f'Only {item.batch.quantity_net} {item.batch.product.unit} available for '
                    f'{item.batch.product.name}.',
                )
                return redirect('marketplace:cart')

        # Create the Order.
        order = Order.objects.create(
            buyer=request.user if request.user.is_authenticated else None,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            buyer_phone=buyer_phone,
            buyer_address=buyer_address,
            total_amount=total_amount,
            notes=notes,
            status='pending',
        )

        # Transfer cart items to order items.
        for item in items:
            OrderItem.objects.create(
                order=order,
                batch=item.batch,
                product_name=item.batch.product.name,
                batch_code=item.batch.batch_code,
                quantity=item.quantity,
                unit_price=item.batch.unit_price,
                subtotal=item.subtotal,
            )
            item.batch.quantity_available -= item.quantity
            if item.batch.quantity_available <= 0:
                item.batch.quantity_available = Decimal('0')
                item.batch.status = 'out_of_stock'
                item.batch.save(update_fields=['quantity_available', 'status'])
            else:
                update_fields = ['quantity_available']
                if item.batch.quantity_available <= 10:
                    item.batch.status = 'low_stock'
                    update_fields.append('status')
                item.batch.save(update_fields=update_fields)

        # Clear the cart.
        cart.items.all().delete()

        messages.success(
            request,
            f'Order {order.order_number} placed successfully. '
            'You will receive a confirmation email shortly.',
        )
        return redirect('marketplace:order_detail', order_number=order.order_number)


class OrderDetailView(DetailView):
    """
    Detail page for a specific order, looked up by order_number.
    """

    model = Order
    template_name = 'marketplace/order_detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        return get_object_or_404(Order, order_number=self.kwargs['order_number'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['page_title'] = f'Order {order.order_number}'
        context['order_items'] = order.items.all()
        return context


class OrderListView(LoginRequiredMixin, ListView):
    """
    Authenticated user's order history.
    """

    model = Order
    template_name = 'marketplace/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .prefetch_related('items')
            .order_by('-placed_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Orders'
        return context

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.approvals.models import ApprovalRequest
from apps.marketplace.models import Order

from .models import Product


class SellerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Summary dashboard for a seller: their products, recent orders, pending approvals.
    """

    template_name = 'seller/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # All non-deleted products belonging to the user's groups.
        user_products = Product.objects.filter(
            created_by=user,
            is_deleted=False,
        ).select_related('group', 'category')

        # Count recent orders (last 30 days) that contain the seller's products.
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_order_count = (
            Order.objects.filter(
                items__batch__product__created_by=user,
                placed_at__gte=thirty_days_ago,
            )
            .distinct()
            .count()
        )

        # Pending approval requests submitted by this user.
        pending_approvals = ApprovalRequest.objects.filter(
            requested_by=user,
            status='pending',
        ).order_by('-requested_at')

        context.update(
            {
                'page_title': 'Seller Dashboard',
                'products': user_products,
                'product_count': user_products.count(),
                'draft_count': user_products.filter(status='draft').count(),
                'published_count': user_products.filter(status='published').count(),
                'review_count': user_products.filter(status='review').count(),
                'recent_order_count': recent_order_count,
                'pending_approvals': pending_approvals,
                'pending_approval_count': pending_approvals.count(),
            }
        )
        return context


class ProductListView(LoginRequiredMixin, ListView):
    """
    Seller's own product list, filtered to their user account.
    """

    template_name = 'seller/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        return (
            Product.objects.filter(
                created_by=self.request.user,
                is_deleted=False,
            )
            .select_related('group', 'category')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Products'
        return context


class ProductDetailView(DetailView):
    """
    Public-facing product detail (also used by sellers for their own product preview).
    """

    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_deleted=False).select_related('group', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['page_title'] = product.name
        context['images'] = product.images.all()
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new product as a draft.  Sets created_by to the current user.
    """

    model = Product
    fields = [
        'name',
        'group',
        'category',
        'scientific_name',
        'description',
        'price',
        'unit',
        'harvest_season',
    ]
    template_name = 'seller/product_form.html'

    def get_success_url(self):
        return reverse_lazy('products:detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add New Product'
        context['action'] = 'Create'
        return context


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit an existing product.  Only the creator or staff may edit.
    """

    model = Product
    fields = [
        'name',
        'group',
        'category',
        'scientific_name',
        'description',
        'price',
        'unit',
        'harvest_season',
    ]
    template_name = 'seller/product_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Non-staff users may only edit their own products.
        qs = Product.objects.filter(is_deleted=False)
        if not self.request.user.is_staff:
            qs = qs.filter(created_by=self.request.user)
        return qs

    def get_success_url(self):
        return reverse_lazy('products:detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.name}'
        context['action'] = 'Update'
        return context


class ProductSubmitView(LoginRequiredMixin, View):
    """
    POST-only view that transitions a product from 'draft' to 'review' and
    creates a corresponding ApprovalRequest for officer/admin action.
    """

    http_method_names = ['post']

    def post(self, request, slug):
        product = get_object_or_404(
            Product,
            slug=slug,
            is_deleted=False,
            created_by=request.user,
        )

        if product.status not in ('draft', 'approved'):
            messages.warning(
                request,
                f'Product "{product.name}" cannot be submitted from its current '
                f'status ({product.get_status_display()}).',
            )
            return redirect('products:detail', slug=slug)

        # Transition status.
        product.status = 'review'
        product.save(update_fields=['status', 'updated_at'])

        # Create or reuse an approval request using the generic content-type framework.
        # The approvals signal also watches product status transitions, so this must
        # be idempotent.
        content_type = ContentType.objects.get_for_model(Product)
        ApprovalRequest.objects.get_or_create(
            content_type=content_type,
            object_id=str(product.pk),
            request_type='product_approval',
            status='pending',
            defaults={
                'object_repr': str(product),
                'requested_by': request.user,
                'notes': f'Product "{product.name}" submitted for review by {request.user.full_name}.',
            },
        )

        messages.success(
            request,
            f'"{product.name}" has been submitted for review.  '
            'You will be notified once a decision is made.',
        )
        return redirect('products:detail', slug=slug)

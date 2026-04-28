from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import HarvestBatch, InventoryBatch


class InventoryBatchListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/batches.html'
    context_object_name = 'batches'
    paginate_by = 25

    def get_queryset(self):
        queryset = InventoryBatch.objects.select_related('product', 'product__group').order_by('-created_at')
        if not self.request.user.is_staff:
            queryset = queryset.filter(product__created_by=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Inventory Batches'
        return context


class HarvestBatchListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/harvest_batches.html'
    context_object_name = 'harvest_batches'
    paginate_by = 25

    def get_queryset(self):
        queryset = HarvestBatch.objects.select_related('group', 'officer').order_by('-harvest_date')
        if self.request.user.role == 'seller':
            queryset = queryset.filter(group__members__user=self.request.user, group__members__is_active=True)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Harvest Batches'
        return context

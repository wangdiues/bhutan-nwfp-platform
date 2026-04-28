from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .models import NWFPGroup


class GroupListView(ListView):
    """
    Public list of all active, non-deleted NWFP groups.
    """

    queryset = NWFPGroup.objects.filter(is_deleted=False, status='active').order_by('name')
    template_name = 'groups/list.html'
    context_object_name = 'groups'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'NWFP Collector Groups'
        context['total_count'] = self.get_queryset().count()
        return context


class GroupDetailView(DetailView):
    """
    Public detail page for a single NWFP group, looked up by slug.
    """

    model = NWFPGroup
    template_name = 'groups/detail.html'
    context_object_name = 'group'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return NWFPGroup.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context['page_title'] = group.name
        context['members'] = group.members.filter(is_active=True).select_related('user')
        context['products'] = group.products.filter(
            status='published', is_deleted=False
        ).order_by('-created_at')[:8]
        return context


class GroupCreateView(LoginRequiredMixin, CreateView):
    """
    Authenticated users can register a new NWFP group.
    """

    model = NWFPGroup
    fields = [
        'name',
        'dzongkhag',
        'gewog',
        'village',
        'description',
        'contact_email',
        'contact_phone',
    ]
    template_name = 'groups/form.html'

    def get_success_url(self):
        return reverse_lazy('groups:detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # New groups are pending approval by default (model default).
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Register a New Group'
        context['action'] = 'Create'
        return context


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    """
    Group leaders / admin can edit group details.
    """

    model = NWFPGroup
    fields = [
        'name',
        'dzongkhag',
        'gewog',
        'village',
        'description',
        'contact_email',
        'contact_phone',
    ]
    template_name = 'groups/form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return NWFPGroup.objects.filter(is_deleted=False)

    def get_success_url(self):
        return reverse_lazy('groups:detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.name}'
        context['action'] = 'Update'
        return context

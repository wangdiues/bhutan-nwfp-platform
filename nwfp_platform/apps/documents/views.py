import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .models import Document

# Mapping from file extension to Document file_type choice value.
EXTENSION_TO_FILE_TYPE = {
    '.pdf': 'pdf',
    '.csv': 'csv',
    '.geojson': 'geojson',
    '.json': 'geojson',
    '.shp': 'shapefile',
    '.zip': 'shapefile',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.webp': 'image',
}


def _detect_file_type(filename):
    """Return a Document file_type value inferred from the file extension."""
    ext = os.path.splitext(filename)[1].lower()
    return EXTENSION_TO_FILE_TYPE.get(ext, 'other')


class DocumentListView(LoginRequiredMixin, ListView):
    """
    List documents scoped to the current user's group memberships.
    """

    template_name = 'documents/list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        # Collect all groups the user belongs to.
        user_group_ids = user.group_memberships.filter(
            is_active=True
        ).values_list('group_id', flat=True)

        return (
            Document.objects.filter(group_id__in=user_group_ids)
            .select_related('group', 'uploaded_by')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Documents'
        return context


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """
    Upload a new document.  Sets uploaded_by to the current user and
    auto-detects file_type from the uploaded file extension.
    """

    model = Document
    fields = ['title', 'file', 'file_type', 'description', 'group', 'product']
    template_name = 'documents/upload.html'

    def get_success_url(self):
        return reverse_lazy('documents:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        document = form.save(commit=False)
        document.uploaded_by = self.request.user

        # Override file_type if not explicitly provided or if the detected
        # type differs — always trust the actual file extension.
        uploaded_file = form.cleaned_data.get('file')
        if uploaded_file:
            detected_type = _detect_file_type(uploaded_file.name)
            # Only override when the user left the default ('other') or when
            # we can make a better determination.
            if document.file_type == 'other' or not document.file_type:
                document.file_type = detected_type

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Upload Document'
        return context


class DocumentDetailView(DetailView):
    """
    Detail view for a single document.
    """

    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        context['certificates'] = self.object.certificates.all()
        return context

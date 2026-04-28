from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import UserRegistrationForm
from .models import User


class RegisterView(CreateView):
    """
    Public registration page.  On success, redirect to the marketplace home.
    """

    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('marketplace:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create an account'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Authenticated users can update their own profile details.
    """

    model = User
    fields = ['full_name', 'phone', 'dzongkhag', 'profile_image']
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        # Always edit the currently authenticated user — ignore any pk/slug in URL.
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Profile'
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Apply Bootstrap classes to all rendered widgets.
        for field in form.fields.values():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            if widget.__class__.__name__ == 'Select':
                widget.attrs['class'] = (existing + ' form-select').strip()
            elif widget.__class__.__name__ == 'ClearableFileInput':
                widget.attrs['class'] = (existing + ' form-control').strip()
            else:
                widget.attrs['class'] = (existing + ' form-control').strip()
        return form

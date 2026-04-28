from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.template import TemplateDoesNotExist


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()
    permission_denied_template = '403.html'

    def has_permission(self):
        user = self.request.user
        return user.is_authenticated and getattr(user, 'role', None) in self.allowed_roles

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        try:
            return render(self.request, self.permission_denied_template, status=403)
        except TemplateDoesNotExist:
            raise PermissionDenied


class SellerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('seller', 'officer', 'admin')


class OfficerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('officer', 'admin')


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('admin',)

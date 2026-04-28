from django.conf import settings
from django.contrib.contenttypes.models import ContentType


STATE_CHANGING_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


def _get_audit_log_model():
    try:
        from apps.accounts.models import AuditLog
    except ImportError:
        from apps.approvals.models import AuditLog
    return AuditLog


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',', 1)[0].strip()
    return request.META.get('REMOTE_ADDR')


class AuditMiddleware:
    """
    Records lightweight audit entries for authenticated state-changing requests.
    Successful login POSTs are recorded as ``login``; other mutating requests are
    recorded as ``update`` so the audit trail stays compact.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._log_request(request, response)
        return response

    def _log_request(self, request, response):
        user = getattr(request, 'user', None)
        if request.method not in STATE_CHANGING_METHODS:
            return
        if not user or not user.is_authenticated:
            return
        if response.status_code >= 500:
            return

        login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
        action = 'login' if request.path == login_url and response.status_code in range(200, 400) else 'update'

        try:
            content_type = ContentType.objects.get_for_model(user, for_concrete_model=False)
            AuditLog = _get_audit_log_model()
            AuditLog.objects.create(
                user=user,
                action=action,
                content_type=content_type,
                object_id=str(user.pk),
                object_repr=str(user),
                changes={
                    'method': request.method,
                    'path': request.get_full_path(),
                    'status_code': response.status_code,
                },
                ip_address=_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
        except Exception:
            # Audit logging must never break the user-facing request path.
            return

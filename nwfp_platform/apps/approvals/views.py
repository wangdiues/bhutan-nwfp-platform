import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.groups.models import NWFPGroup

from .models import ApprovalRequest, AuditLog, Notification

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_audit_log(user, action, obj=None, changes=None, request=None):
    """
    Convenience wrapper to create an AuditLog entry.
    """
    ct = None
    obj_id = ''
    obj_repr = ''

    if obj is not None:
        ct = ContentType.objects.get_for_model(obj)
        obj_id = str(obj.pk)
        obj_repr = str(obj)

    ip_address = None
    user_agent = ''
    if request is not None:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=ct,
        object_id=obj_id,
        object_repr=obj_repr,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ---------------------------------------------------------------------------
# Management dashboard
# ---------------------------------------------------------------------------


class ManagementDashboardView(LoginRequiredMixin, TemplateView):
    """
    High-level dashboard for officers and administrators.
    """

    template_name = 'management/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        pending_approvals_count = ApprovalRequest.objects.filter(status='pending').count()
        active_groups_count = NWFPGroup.objects.filter(
            is_deleted=False, status='active'
        ).count()
        recent_audit_logs = AuditLog.objects.select_related('user').order_by(
            '-timestamp'
        )[:10]
        unread_notifications = Notification.objects.filter(
            recipient=user, is_read=False
        ).order_by('-created_at')

        context.update(
            {
                'page_title': 'Management Dashboard',
                'pending_approvals_count': pending_approvals_count,
                'active_groups_count': active_groups_count,
                'recent_audit_logs': recent_audit_logs,
                'unread_notifications': unread_notifications,
                'unread_notification_count': unread_notifications.count(),
            }
        )
        return context


# ---------------------------------------------------------------------------
# Approval queue
# ---------------------------------------------------------------------------


class ApprovalQueueView(LoginRequiredMixin, ListView):
    """
    List of pending ApprovalRequests awaiting a decision.
    """

    template_name = 'management/approval_queue.html'
    context_object_name = 'approval_requests'
    paginate_by = 20

    def get_queryset(self):
        return (
            ApprovalRequest.objects.filter(status='pending')
            .select_related('requested_by', 'assigned_to', 'content_type')
            .order_by('-requested_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Approval Queue'
        return context


class ApprovalDecideView(LoginRequiredMixin, View):
    """
    POST-only view: approve or reject an ApprovalRequest.

    Expected POST fields:
        decision  -- 'approved' or 'rejected'
        notes     -- optional decision notes
    """

    http_method_names = ['post']

    @transaction.atomic
    def post(self, request, pk):
        approval = get_object_or_404(ApprovalRequest, pk=pk)

        if approval.status != 'pending':
            messages.warning(
                request,
                f'Approval request {pk} has already been decided ({approval.status}).',
            )
            return redirect('approvals:queue')

        decision = request.POST.get('decision', '').strip().lower()
        if decision not in ('approved', 'rejected'):
            messages.error(request, 'Invalid decision.  Must be "approved" or "rejected".')
            return redirect('approvals:queue')

        notes = request.POST.get('notes', '').strip()

        # Record the decision on the ApprovalRequest.
        approval.status = decision
        approval.decision_notes = notes
        approval.decided_at = timezone.now()
        approval.assigned_to = request.user
        approval.save(update_fields=['status', 'decision_notes', 'decided_at', 'assigned_to'])

        # Attempt to reflect the decision on the target object.
        target_obj = None
        try:
            target_obj = approval.content_object
        except Exception:
            logger.warning('Could not resolve content_object for ApprovalRequest %s', pk)

        if target_obj is not None:
            self._apply_decision_to_target(target_obj, decision, approval.request_type)

        # Create an audit log entry.
        _create_audit_log(
            user=request.user,
            action='approve' if decision == 'approved' else 'reject',
            obj=approval,
            changes={'decision': decision, 'notes': notes},
            request=request,
        )

        # Notify the requester.
        verb = 'approved' if decision == 'approved' else 'rejected'
        Notification.objects.create(
            recipient=approval.requested_by,
            title=f'Your {approval.get_request_type_display()} has been {verb}',
            message=(
                f'Your request for "{approval.object_repr}" was {verb} '
                f'by {request.user.full_name}.'
                + (f'  Notes: {notes}' if notes else '')
            ),
            notification_type='approval_done',
            related_url=request.path,
        )

        messages.success(
            request,
            f'ApprovalRequest for "{approval.object_repr}" has been {verb}.',
        )
        return redirect('approvals:queue')

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_decision_to_target(obj, decision, request_type):
        """
        Update the target object's status field to reflect the decision.
        """
        # Products: approved -> 'approved', rejected -> back to 'draft'
        if request_type == 'product_approval':
            from apps.products.models import Product
            if isinstance(obj, Product):
                new_status = 'approved' if decision == 'approved' else 'draft'
                obj.status = new_status
                obj.save(update_fields=['status', 'updated_at'])

        # Groups: approved -> 'active', rejected -> stays 'pending'
        elif request_type == 'group_registration':
            if isinstance(obj, NWFPGroup):
                if decision == 'approved':
                    obj.status = 'active'
                    obj.save(update_fields=['status', 'updated_at'])

        # Documents: approved -> 'processed', rejected -> 'failed'
        elif request_type == 'document_validation':
            from apps.documents.models import Document
            if isinstance(obj, Document):
                new_status = 'processed' if decision == 'approved' else 'failed'
                obj.status = new_status
                obj.save(update_fields=['status'])


# ---------------------------------------------------------------------------
# Group registry
# ---------------------------------------------------------------------------


class GroupRegistryView(LoginRequiredMixin, ListView):
    """
    Officer/admin view of all registered NWFP groups with filtering support.
    """

    model = NWFPGroup
    template_name = 'management/group_registry.html'
    context_object_name = 'groups'
    paginate_by = 20

    def get_queryset(self):
        qs = NWFPGroup.objects.filter(is_deleted=False).order_by('name')

        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)

        dzongkhag = self.request.GET.get('dzongkhag', '').strip()
        if dzongkhag:
            qs = qs.filter(dzongkhag=dzongkhag)

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Group Registry'
        context['filter_params'] = self.request.GET
        return context


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


class AuditLogView(LoginRequiredMixin, ListView):
    """
    Chronological audit trail of all significant actions in the platform.
    """

    model = AuditLog
    template_name = 'management/audit_log.html'
    context_object_name = 'audit_logs'
    paginate_by = 50

    def get_queryset(self):
        return AuditLog.objects.select_related('user', 'content_type').order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Audit Log'
        return context


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Lists all notifications for the current user and marks them as read.
    """

    template_name = 'management/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        # Mark all unread notifications as read when the user views this page.
        Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Notifications'
        return context

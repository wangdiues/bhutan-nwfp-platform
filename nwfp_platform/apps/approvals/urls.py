from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    path('', views.ManagementDashboardView.as_view(), name='dashboard'),
    path('approvals/', views.ApprovalQueueView.as_view(), name='queue'),
    path('approvals/<uuid:pk>/decide/', views.ApprovalDecideView.as_view(), name='decide'),
    path('groups/', views.GroupRegistryView.as_view(), name='group_registry'),
    path('audit/', views.AuditLogView.as_view(), name='audit_log'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
]

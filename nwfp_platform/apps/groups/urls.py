from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.GroupListView.as_view(), name='list'),
    # 'create/' must be declared BEFORE '<slug:slug>/' so it is matched first.
    path('create/', views.GroupCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.GroupDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.GroupUpdateView.as_view(), name='edit'),
]

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Seller dashboard
    path('dashboard/', views.SellerDashboardView.as_view(), name='dashboard'),

    # Product management — 'create/' before '<slug:slug>/' to avoid mis-routing.
    path('products/', views.ProductListView.as_view(), name='list'),
    path('products/create/', views.ProductCreateView.as_view(), name='create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('products/<slug:slug>/edit/', views.ProductUpdateView.as_view(), name='edit'),
    path('products/<slug:slug>/submit/', views.ProductSubmitView.as_view(), name='submit'),
]

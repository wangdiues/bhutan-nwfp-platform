from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.MarketplaceHomeView.as_view(), name='home'),
    path('products/', views.ProductCatalogueView.as_view(), name='catalogue'),
    path('products/<slug:slug>/', views.ProductDetailPublicView.as_view(), name='product_detail'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.CartAddView.as_view(), name='cart_add'),
    path('cart/remove/<int:item_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
]

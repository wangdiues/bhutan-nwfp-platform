from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('groups', views.GroupViewSet, basename='group')
router.register('orders', views.OrderViewSet, basename='order')
router.register('harvest-batches', views.HarvestBatchViewSet, basename='harvest-batch')
router.register('resource-sites', views.ResourceSiteViewSet, basename='resource-site')

urlpatterns = [
    path('', include(router.urls)),
]

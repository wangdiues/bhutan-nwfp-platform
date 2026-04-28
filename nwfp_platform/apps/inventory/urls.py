from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('inventory/', views.InventoryBatchListView.as_view(), name='batches'),
    path('harvests/', views.HarvestBatchListView.as_view(), name='harvest_batches'),
]

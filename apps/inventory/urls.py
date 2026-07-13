from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'),
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/create/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),
    path('waste/', views.waste_list, name='waste_list'),
    path('waste/create/', views.waste_create, name='waste_create'),
    path('waste/<int:pk>/delete/', views.waste_delete, name='waste_delete'),
    path('returns/', views.return_list, name='return_list'),
    path('returns/create/', views.return_create, name='return_create'),
    path('returns/<int:pk>/delete/', views.return_delete, name='return_delete'),
    path('product-inventory/', views.product_inventory_list, name='product_inventory_list'),
    path('product-inventory/<int:pk>/', views.product_inventory_detail, name='product_inventory_detail'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('product-purchases/', views.product_purchase_list, name='product_purchase_list'),
    path('product-purchases/create/', views.product_purchase_create, name='product_purchase_create'),
    path('product-purchases/<int:pk>/delete/', views.product_purchase_delete, name='product_purchase_delete'),
]

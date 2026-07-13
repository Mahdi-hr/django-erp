from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('recalculate/', views.recalculate_all_costs, name='recalculate_all_costs'),
    path('api/prices/', views.api_material_prices, name='api_material_prices'),
    path('export/employer/excel/', views.product_export_employer_excel, name='product_export_employer_excel'),
    path('export/customer/excel/', views.product_export_customer_excel, name='product_export_customer_excel'),
    path('print/employer/', views.product_print_employer, name='product_print_employer'),
    path('print/customer/', views.product_print_customer, name='product_print_customer'),
]

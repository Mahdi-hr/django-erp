from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('<int:pk>/pay/', views.invoice_register_payment, name='invoice_register_payment'),
    path('<int:pk>/print/dark/', views.invoice_print_dark, name='invoice_print_dark'),
    path('<int:pk>/print/light/', views.invoice_print_light, name='invoice_print_light'),
]

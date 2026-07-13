from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/start/', views.order_start, name='order_start'),
    path('orders/<int:pk>/complete/', views.order_complete, name='order_complete'),
    path('orders/<int:pk>/cancel/', views.order_cancel, name='order_cancel'),
    path('daily/', views.daily_production_list, name='daily_production_list'),
    path('daily/create/', views.daily_production_create, name='daily_production_create'),
    path('daily/<int:pk>/edit/', views.daily_production_edit, name='daily_production_edit'),
    path('daily/<int:pk>/delete/', views.daily_production_delete, name='daily_production_delete'),
]

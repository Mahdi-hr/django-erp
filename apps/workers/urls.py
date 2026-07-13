from django.urls import path
from . import views

urlpatterns = [
    path('', views.worker_list, name='worker_list'),
    path('create/', views.worker_create, name='worker_create'),
    path('<int:pk>/', views.worker_detail, name='worker_detail'),
    path('<int:pk>/edit/', views.worker_edit, name='worker_edit'),
    path('<int:pk>/delete/', views.worker_delete, name='worker_delete'),
]

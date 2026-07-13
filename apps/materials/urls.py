from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('', views.material_list, name='material_list'),
    path('create/', views.material_create, name='material_create'),
    path('<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('<int:pk>/', views.material_detail, name='material_detail'),
    path('export/excel/', views.material_export_excel, name='material_export_excel'),
    path('print/', views.material_print, name='material_print'),
]

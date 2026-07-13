from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_dashboard, name='settings_dashboard'),
    path('theme/', views.theme_customizer, name='theme_customizer'),
    path('theme/save-ajax/', views.theme_save_ajax, name='theme_save_ajax'),
    path('<int:pk>/edit/', views.setting_edit, name='setting_edit'),
    path('fixed-costs/create/', views.fixed_cost_create, name='fixed_cost_create'),
    path('fixed-costs/<int:pk>/edit/', views.fixed_cost_edit, name='fixed_cost_edit'),
    path('fixed-costs/<int:pk>/delete/', views.fixed_cost_delete, name='fixed_cost_delete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.updater_dashboard, name='updater_dashboard'),
    path('check/', views.check_updates, name='check_updates'),
    path('update/', views.perform_update, name='perform_update'),
    path('rollback/', views.rollback_update, name='rollback'),
    path('history/', views.version_history, name='history'),
    path('backups/', views.backup_list, name='backups'),
]

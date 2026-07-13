from django.urls import path
from . import views

urlpatterns = [
    path('', views.backup_dashboard, name='backup_dashboard'),
    path('export/full/', views.backup_full_export, name='backup_full_export'),
    path('export/partial/', views.backup_partial_export, name='backup_partial_export'),
    path('restore/', views.backup_restore, name='backup_restore'),
    path('<int:pk>/download/', views.backup_download, name='backup_download'),
    path('<int:pk>/delete/', views.backup_delete, name='backup_delete'),
    path('<int:pk>/metadata/', views.backup_metadata, name='backup_metadata'),
]

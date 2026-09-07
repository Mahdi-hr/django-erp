from django.urls import path
from . import views

urlpatterns = [
    path('', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]

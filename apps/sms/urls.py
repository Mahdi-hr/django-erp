from django.urls import path
from . import views

urlpatterns = [
    path('', views.sms_dashboard, name='sms_dashboard'),
    path('quick-settings/', views.sms_quick_settings, name='sms_quick_settings'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('send/', views.send_sms, name='send_sms'),
    path('send-bulk/', views.send_bulk_sms, name='send_bulk_sms'),
    path('messages/', views.message_list, name='message_list'),
    path('messages/<int:pk>/delete/', views.delete_message, name='delete_message'),
    path('messages/delete-all/', views.delete_all_messages, name='delete_all_messages'),
    path('providers/', views.provider_config, name='provider_config'),
    path('providers/<int:pk>/edit/', views.provider_config_edit, name='provider_config_edit'),
    path('providers/<int:pk>/test/', views.test_provider_api, name='test_provider_api'),
    path('providers/<int:pk>/activate/', views.activate_provider, name='activate_provider'),
    path('reports/today/', views.sms_report_today, name='sms_report_today'),
    path('reports/credit/', views.sms_report_credit, name='sms_report_credit'),
    path('reports/lines/', views.sms_report_lines, name='sms_report_lines'),
    path('reports/received/', views.sms_report_received, name='sms_report_received'),
]

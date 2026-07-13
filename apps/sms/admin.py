from django.contrib import admin
from .models import SMSTemplate, SMSProviderConfig, SMSMessage


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'title']


@admin.register(SMSProviderConfig)
class SMSProviderConfigAdmin(admin.ModelAdmin):
    list_display = ['provider', 'sender_number', 'is_active']
    list_filter = ['is_active']


@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ['phone', 'customer', 'status', 'provider', 'sent_at']
    list_filter = ['status', 'provider']
    search_fields = ['phone', 'message']

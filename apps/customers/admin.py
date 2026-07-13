from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'phone', 'city', 'balance', 'is_active']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'company', 'phone']

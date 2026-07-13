from django.contrib import admin
from .models import FixedCost


@admin.register(FixedCost)
class FixedCostAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount', 'category', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['name']

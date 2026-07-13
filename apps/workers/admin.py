from django.contrib import admin
from .models import Worker


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'phone']

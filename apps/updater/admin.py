from django.contrib import admin
from .models import UpdateLog


@admin.register(UpdateLog)
class UpdateLogAdmin(admin.ModelAdmin):
    list_display = [
        'version_from', 'version_to', 'status', 'triggered_by',
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'started_at']
    readonly_fields = [
        'version_from', 'version_to', 'status', 'backup_path',
        'error_message', 'started_at', 'completed_at', 'triggered_by'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

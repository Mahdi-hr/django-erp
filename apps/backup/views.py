"""
Backup views - Controller layer.
All business logic is delegated to services.
"""
import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils import timezone

from .models import BackupLog
from .services.registry import BACKUP_SECTIONS, get_all_sections
from .services.export_service import export_full_backup
from .services.import_service import import_update_mode, import_replace_mode, ImportResult
from .services.metadata import generate_metadata, generate_version_info, validate_metadata
from .services.zip_manager import create_backup_zip, read_backup_zip, verify_checksum
from .services.validators import validate_backup_file, validate_restore_data
from .services.utils import format_file_size, ensure_backup_dir, get_backup_filename


def is_admin(user):
    """Check if user is admin."""
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_admin)
def backup_dashboard(request):
    """Main backup dashboard page."""
    sections = get_all_sections()

    # Get model counts for each section
    section_data = []
    for key, section in sections.items():
        total = 0
        models_info = []
        for app_label, model_name in section['models']:
            try:
                from django.apps import apps
                model_class = apps.get_model(app_label, model_name)
                count = model_class.objects.count()
                total += count
                models_info.append({
                    'name': model_name,
                    'app': app_label,
                    'count': count,
                })
            except LookupError:
                models_info.append({
                    'name': model_name,
                    'app': app_label,
                    'count': 0,
                })
        section_data.append({
            'key': key,
            'label': section['label'],
            'icon': section['icon'],
            'total': total,
            'models': models_info,
        })

    # Recent backups
    recent_backups = BackupLog.objects.all()[:20]

    return render(request, 'backup/backup_dashboard.html', {
        'sections': section_data,
        'recent_backups': recent_backups,
    })


@login_required
@user_passes_test(is_admin)
def backup_full_export(request):
    """Export a full backup."""
    try:
        # Export all data
        backup_data, record_counts = export_full_backup()

        # Generate metadata
        metadata = generate_metadata(
            record_counts=record_counts,
            created_by=request.user.username,
            backup_type='full',
            sections=list(BACKUP_SECTIONS.keys()),
        )

        # Generate version info
        version_info = generate_version_info()

        # Create ZIP
        backup_dir = ensure_backup_dir()
        filename = get_backup_filename('full')
        filepath = os.path.join(backup_dir, filename)

        filepath, file_size, checksum = create_backup_zip(
            backup_data, metadata, version_info, filepath
        )

        # Log the backup
        BackupLog.objects.create(
            backup_type='full_backup',
            status='success',
            filename=filename,
            file_size=file_size,
            record_count=metadata.get('total_records', 0),
            backup_version=metadata.get('backup_version', '1.0'),
            metadata_json=json.dumps(metadata, default=str, ensure_ascii=False),
            created_by=request.user,
        )

        messages.success(request, f'بکاپ کامل با موفقیت ایجاد شد ({format_file_size(file_size)})')
        return redirect('backup_dashboard')

    except Exception as e:
        BackupLog.objects.create(
            backup_type='full_backup',
            status='failed',
            error_count=1,
            errors_detail=str(e),
            created_by=request.user,
        )
        messages.error(request, f'خطا در ایجاد بکاپ: {str(e)}')
        return redirect('backup_dashboard')


@login_required
@user_passes_test(is_admin)
def backup_partial_export(request):
    """Export a partial backup with selected sections."""
    if request.method != 'POST':
        return redirect('backup_dashboard')

    selected_sections = request.POST.getlist('sections')
    if not selected_sections:
        messages.error(request, 'هیچ بخشی انتخاب نشده است')
        return redirect('backup_dashboard')

    try:
        # Export selected sections
        backup_data, record_counts = export_full_backup(sections=selected_sections)

        # Generate metadata
        metadata = generate_metadata(
            record_counts=record_counts,
            created_by=request.user.username,
            backup_type='partial',
            sections=selected_sections,
        )

        # Generate version info
        version_info = generate_version_info()

        # Create ZIP
        backup_dir = ensure_backup_dir()
        filename = get_backup_filename('partial')
        filepath = os.path.join(backup_dir, filename)

        filepath, file_size, checksum = create_backup_zip(
            backup_data, metadata, version_info, filepath
        )

        # Log the backup
        BackupLog.objects.create(
            backup_type='partial_backup',
            status='success',
            filename=filename,
            file_size=file_size,
            record_count=metadata.get('total_records', 0),
            backup_version=metadata.get('backup_version', '1.0'),
            metadata_json=json.dumps(metadata, default=str, ensure_ascii=False),
            created_by=request.user,
        )

        messages.success(request, f'بکاپ جزئی با موفقیت ایجاد شد ({format_file_size(file_size)})')
        return redirect('backup_dashboard')

    except Exception as e:
        BackupLog.objects.create(
            backup_type='partial_backup',
            status='failed',
            error_count=1,
            errors_detail=str(e),
            created_by=request.user,
        )
        messages.error(request, f'خطا در ایجاد بکاپ: {str(e)}')
        return redirect('backup_dashboard')


@login_required
@user_passes_test(is_admin)
def backup_restore(request):
    """Restore from a backup file."""
    if request.method != 'POST':
        return redirect('backup_dashboard')

    backup_file = request.FILES.get('backup_file')
    mode = request.POST.get('mode', 'update')

    if not backup_file:
        messages.error(request, 'فایل بکاپ انتخاب نشده است')
        return redirect('backup_dashboard')

    try:
        # Read and validate the ZIP
        file_content = backup_file.read()
        is_valid, error_msg = validate_backup_file(file_content)
        if not is_valid:
            messages.error(request, f'فایل بکاپ نامعتبر: {error_msg}')
            return redirect('backup_dashboard')

        # Extract data from ZIP
        import io
        import zipfile

        with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
            backup_data = json.loads(zf.read('backup.json').decode('utf-8'))
            metadata = json.loads(zf.read('metadata.json').decode('utf-8'))

        # Validate data
        data_valid, data_errors = validate_restore_data(backup_data, metadata)
        if not data_valid:
            for err in data_errors[:5]:
                messages.error(request, err)
            return redirect('backup_dashboard')

        # Perform restore
        result = ImportResult()
        if mode == 'replace':
            result = import_replace_mode(backup_data, result)
        else:
            result = import_update_mode(backup_data, result)

        # Log the restore
        BackupLog.objects.create(
            backup_type='restore_replace' if mode == 'replace' else 'restore_update',
            status='success' if result.errors == 0 else 'partial',
            filename=backup_file.name,
            file_size=file_content.__len__(),
            record_count=result.total_records,
            imported_count=result.imported,
            updated_count=result.updated,
            deleted_count=result.deleted,
            error_count=result.errors,
            errors_detail='\n'.join(result.error_details[:20]),
            backup_version=metadata.get('backup_version', '1.0'),
            metadata_json=json.dumps(metadata, default=str, ensure_ascii=False),
            created_by=request.user,
        )

        # Show results
        if result.errors == 0:
            msg = f'بازیابی موفق: {result.imported} رکورد وارد شد'
            if result.updated:
                msg += f'، {result.updated} رکورد بروزرسانی شد'
            if result.deleted:
                msg += f'، {result.deleted} رکورد حذف شد'
            messages.success(request, msg)
        else:
            msg = f'بازیابی با {result.errors} خطا انجام شد'
            messages.warning(request, msg)
            for err in result.error_details[:3]:
                messages.error(request, err)

        return redirect('backup_dashboard')

    except Exception as e:
        BackupLog.objects.create(
            backup_type='restore_update',
            status='failed',
            filename=backup_file.name if backup_file else '',
            error_count=1,
            errors_detail=str(e),
            created_by=request.user,
        )
        messages.error(request, f'خطا در بازیابی: {str(e)}')
        return redirect('backup_dashboard')


@login_required
@user_passes_test(is_admin)
def backup_download(request, pk):
    """Download a backup file."""
    log = get_object_or_404(BackupLog, pk=pk)
    from django.conf import settings
    filepath = os.path.join(settings.MEDIA_ROOT, 'backups', log.filename)

    if not os.path.exists(filepath):
        messages.error(request, 'فایل بکاپ یافت نشد')
        return redirect('backup_dashboard')

    response = FileResponse(open(filepath, 'rb'), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{log.filename}"'
    return response


@login_required
@user_passes_test(is_admin)
def backup_delete(request, pk):
    """Delete a backup file."""
    log = get_object_or_404(BackupLog, pk=pk)
    if request.method == 'POST':
        # Delete the file
        from django.conf import settings
        filepath = os.path.join(settings.MEDIA_ROOT, 'backups', log.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        log.delete()
        messages.success(request, 'بکاپ حذف شد')
    return redirect('backup_dashboard')


@login_required
@user_passes_test(is_admin)
def backup_metadata(request, pk):
    """View backup metadata."""
    log = get_object_or_404(BackupLog, pk=pk)
    try:
        metadata = json.loads(log.metadata_json)
    except (json.JSONDecodeError, TypeError):
        metadata = {}

    return render(request, 'backup/backup_metadata.html', {
        'log': log,
        'metadata': metadata,
    })

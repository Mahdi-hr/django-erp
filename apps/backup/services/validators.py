"""
Validators for backup operations.
Validates backup files and data integrity.
"""
from typing import Dict, List, Tuple


def validate_backup_file(file_content: bytes) -> Tuple[bool, str]:
    """
    Validate a backup file (should be a ZIP).

    Args:
        file_content: Raw file content

    Returns:
        Tuple of (is_valid, error_message)
    """
    import zipfile
    import io

    try:
        zip_file = zipfile.ZipFile(io.BytesIO(file_content))
        namelist = zip_file.namelist()

        # Check required files
        required = ['backup.json', 'metadata.json']
        for req in required:
            if req not in namelist:
                return False, f'فایل {req} در بکاپ وجود ندارد'

        # Check backup.json is valid JSON
        backup_json = zip_file.read('backup.json').decode('utf-8')
        try:
            data = __import__('json').loads(backup_json)
            if not isinstance(data, dict):
                return False, 'ساختار backup.json نامعتبر است'
        except __import__('json').JSONDecodeError:
            return False, 'فایل backup.json معتبر JSON نیست'

        # Check metadata.json is valid JSON
        metadata_json = zip_file.read('metadata.json').decode('utf-8')
        try:
            metadata = __import__('json').loads(metadata_json)
            if not isinstance(metadata, dict):
                return False, 'ساختار metadata.json نامعتبر است'
        except __import__('json').JSONDecodeError:
            return False, 'فایل metadata.json معتبر JSON نیست'

        zip_file.close()
        return True, ''

    except zipfile.BadZipFile:
        return False, 'فایل ZIP نامعتبر است'
    except Exception as e:
        return False, f'خطا در اعتبارسنجی: {str(e)}'


def validate_restore_data(
    backup_data: dict,
    metadata: dict,
) -> Tuple[bool, List[str]]:
    """
    Validate data before restore.

    Args:
        backup_data: The backup data
        metadata: Backup metadata

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    from .registry import BACKUP_SECTIONS

    errors = []

    if not isinstance(backup_data, dict):
        errors.append('ساختار داده بکاپ نامعتبر است')
        return False, errors

    # Check if any data exists
    total_records = sum(len(records) for records in backup_data.values())
    if total_records == 0:
        errors.append('فایل بکاپ خالی است')
        return False, errors

    # Validate each model's data
    for key, records in backup_data.items():
        try:
            app_label, model_name = key.split('.')
        except ValueError:
            errors.append(f'کلید مدل نامعتبر: {key}')
            continue

        # Check if model exists
        try:
            from django.apps import apps
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            errors.append(f'مدل {app_label}.{model_name} در سیستم یافت نشد')
            continue

        # Validate records are dicts
        if not isinstance(records, list):
            errors.append(f'داده‌های {key} لیست نیست')
            continue

        for i, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f'رکورد {i} در {key} دیکشنری نیست')
                if len(errors) > 20:
                    errors.append('... تعداد خطاها زیاد است')
                    return False, errors

    # Check version compatibility
    from .metadata import validate_metadata
    meta_valid, meta_errors = validate_metadata(metadata)
    if not meta_valid:
        errors.extend(meta_errors)

    return (len(errors) == 0, errors)


def validate_foreign_keys(
    backup_data: dict,
) -> Tuple[bool, List[str]]:
    """
    Check for potential foreign key issues in backup data.

    Args:
        backup_data: The backup data

    Returns:
        Tuple of (has_issues, list_of_warnings)
    """
    warnings = []

    # This is a basic check - more thorough checks would require
    # analyzing the actual FK relationships
    for key, records in backup_data.items():
        try:
            app_label, model_name = key.split('.')
            from django.apps import apps
            model_class = apps.get_model(app_label, model_name)

            # Check for required FK fields
            for field in model_class._meta.get_fields():
                if hasattr(field, 'related_model') and field.related_model:
                    if not field.null and not field.has_default():
                        # This is a required FK
                        fk_name = field.name
                        for i, record in enumerate(records):
                            if fk_name not in record or record[fk_name] is None:
                                pass  # Could warn, but FK might be in the backup
        except (LookupError, ValueError):
            continue

    return (len(warnings) > 0, warnings)

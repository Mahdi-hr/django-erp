"""
Metadata service for backup operations.
Generates and validates backup metadata.
"""
import json
import platform
from datetime import datetime
from typing import Dict
from django.conf import settings
from django.utils import timezone


BACKUP_VERSION = '2.0'


def generate_metadata(
    record_counts: Dict[str, int],
    created_by: str,
    backup_type: str = 'full',
    sections: list = None,
) -> dict:
    """
    Generate metadata for a backup file.

    Args:
        record_counts: Dict mapping model keys to record counts
        created_by: Username of the creator
        backup_type: 'full' or 'partial'
        sections: List of section keys included

    Returns:
        Metadata dictionary
    """
    total_records = sum(record_counts.values())

    return {
        'created_at': timezone.now().isoformat(),
        'created_by': created_by,
        'backup_type': backup_type,
        'backup_version': BACKUP_VERSION,
        'system_version': _get_system_version(),
        'django_version': _get_django_version(),
        'python_version': platform.python_version(),
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'platform': platform.platform(),
        'total_records': total_records,
        'record_counts': record_counts,
        'sections': sections or [],
    }


def generate_version_info() -> dict:
    """Generate version compatibility info."""
    return {
        'backup_version': BACKUP_VERSION,
        'min_restore_version': '1.0',
        'django_version': _get_django_version(),
        'python_version': platform.python_version(),
    }


def validate_metadata(metadata: dict) -> tuple:
    """
    Validate backup metadata.

    Returns:
        Tuple of (is_valid: bool, errors: list)
    """
    errors = []

    required_fields = ['created_at', 'backup_version', 'backup_type']
    for field in required_fields:
        if field not in metadata:
            errors.append(f'فیلد الزامی {field} وجود ندارد')

    if 'backup_version' in metadata:
        version = metadata['backup_version']
        if not isinstance(version, str):
            errors.append('نسخه بکاپ نامعتبر است')
        else:
            try:
                major = int(version.split('.')[0])
                if major > int(BACKUP_VERSION.split('.')[0]):
                    errors.append(f'نسخه بکاپ ({version}) بالاتر از نسخه فعلی ({BACKUP_VERSION}) است')
            except (ValueError, IndexError):
                errors.append('فرمت نسخه بکاپ نامعتبر است')

    return (len(errors) == 0, errors)


def _get_system_version() -> str:
    """Get the system version from version.json."""
    import os
    version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), 'version.json')
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('version', '1.0.0')
    except (FileNotFoundError, json.JSONDecodeError):
        return '1.0.0'


def _get_django_version() -> str:
    """Get Django version."""
    import django
    return django.get_version()

"""
Utility functions for backup operations.
"""
import json
import os
from typing import Dict, List


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024.0
    return f'{size_bytes:.1f} TB'


def get_record_summary(record_counts: Dict[str, int]) -> str:
    """
    Generate a summary of record counts.

    Args:
        record_counts: Dict mapping model keys to counts

    Returns:
        Summary string
    """
    total = sum(record_counts.values())
    sections = len(record_counts)
    return f'{total} رکورد در {sections} جدول'


def ensure_backup_dir() -> str:
    """Ensure backup directory exists and return its path."""
    from django.conf import settings
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def get_backup_filename(backup_type: str = 'full') -> str:
    """
    Generate a unique backup filename.

    Args:
        backup_type: 'full' or 'partial'

    Returns:
        Filename string
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'erp_backup_{backup_type}_{timestamp}.zip'


def clean_model_data(records: List[dict], model_class: type) -> List[dict]:
    """
    Clean model data by removing fields that don't exist on the model.

    Args:
        records: List of record dicts
        model_class: Django model class

    Returns:
        Cleaned list of records
    """
    model_fields = {f.name for f in model_class._meta.get_fields()}
    cleaned = []
    for record in records:
        clean = {k: v for k, v in record.items() if k in model_fields}
        cleaned.append(clean)
    return cleaned

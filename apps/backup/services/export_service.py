"""
Export service for backup operations.
Handles extracting data from the database and preparing it for backup.
"""
import json
import platform
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from django.db.models import Model, QuerySet
from django.apps import apps


def export_model_data(model_class: type) -> List[dict]:
    """
    Export all records of a model as a list of dictionaries.

    Args:
        model_class: Django model class

    Returns:
        List of dicts, one per record
    """
    queryset = model_class.objects.all()
    if not queryset.exists():
        return []
    return list(queryset.values())


def export_section_models(model_keys: List[str]) -> Tuple[Dict[str, List[dict]], Dict[str, int]]:
    """
    Export data for a list of model keys.

    Args:
        model_keys: List of 'app_label.ModelName' strings

    Returns:
        Tuple of (data_dict, record_counts)
    """
    data = {}
    counts = {}
    for key in model_keys:
        app_label, model_name = key.split('.')
        try:
            model_class = apps.get_model(app_label, model_name)
            records = export_model_data(model_class)
            data[key] = records
            counts[key] = len(records)
        except (LookupError, Exception) as e:
            data[key] = []
            counts[key] = 0
    return data, counts


def export_full_backup(sections: Optional[List[str]] = None) -> Tuple[Dict[str, List[dict]], Dict[str, int]]:
    """
    Export all data for backup.

    Args:
        sections: Optional list of section keys. If None, export all sections.

    Returns:
        Tuple of (data_dict, record_counts)
    """
    from .registry import BACKUP_SECTIONS, get_section_models

    all_data = {}
    all_counts = {}

    for section_key, section in BACKUP_SECTIONS.items():
        if sections and section_key not in sections:
            continue
        model_keys = [f'{app}.{model}' for app, model in section['models']]
        data, counts = export_section_models(model_keys)
        all_data.update(data)
        all_counts.update(counts)

    return all_data, all_counts

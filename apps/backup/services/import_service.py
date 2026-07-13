"""
Import service for backup restore operations.
Handles importing data back into the database.
"""
import json
from typing import Dict, List, Optional, Set, Tuple
from django.db import transaction, connection
from django.apps import apps
from django.contrib.auth import get_user_model


User = get_user_model()


class ImportResult:
    """Result of an import operation."""

    def __init__(self):
        self.imported = 0
        self.updated = 0
        self.deleted = 0
        self.errors = 0
        self.error_details = []
        self.success_models = []
        self.failed_models = []

    @property
    def total_records(self) -> int:
        return self.imported + self.updated

    def to_dict(self) -> dict:
        return {
            'imported': self.imported,
            'updated': self.updated,
            'deleted': self.deleted,
            'errors': self.errors,
            'error_details': self.error_details,
            'success_models': self.success_models,
            'failed_models': self.failed_models,
        }


def _get_dependency_order(model_keys: List[str]) -> List[str]:
    """
    Sort model keys by dependency — children first, parents last.
    Used for DELETE order.

    Returns:
        Sorted list with children first, parents last
    """
    from django.db.models import ForeignKey, OneToOneField

    references = {}
    all_keys = set(model_keys)

    for key in model_keys:
        try:
            app_label, model_name = key.split('.')
            model_class = apps.get_model(app_label, model_name)
            refs = set()
            for field in model_class._meta.fields:
                if isinstance(field, (ForeignKey, OneToOneField)):
                    if field.related_model:
                        ref_key = f'{field.related_model._meta.app_label}.{field.related_model.__name__}'
                        if ref_key != key and ref_key in all_keys:
                            refs.add(ref_key)
            references[key] = refs
        except (LookupError, ValueError):
            references[key] = set()

    in_degree = {key: 0 for key in model_keys}
    for key, refs in references.items():
        for ref in refs:
            if ref in in_degree:
                in_degree[ref] += 1

    queue = [key for key, deg in in_degree.items() if deg == 0]
    result = []

    while queue:
        queue.sort()
        node = queue.pop(0)
        result.append(node)
        for ref in references.get(node, set()):
            if ref in in_degree:
                in_degree[ref] -= 1
                if in_degree[ref] == 0:
                    queue.append(ref)

    for key in model_keys:
        if key not in result:
            result.append(key)

    return result


def _get_insert_order(model_keys: List[str]) -> List[str]:
    """
    Get the correct order for inserting data — parents first, children last.
    """
    delete_order = _get_dependency_order(model_keys)
    return list(reversed(delete_order))


def import_update_mode(
    backup_data: Dict[str, List[dict]],
    result: Optional[ImportResult] = None,
) -> ImportResult:
    """
    Import data in update mode (upsert).
    Existing records are updated, new ones are inserted.
    No records are deleted. Uses dependency ordering for inserts.
    """
    if result is None:
        result = ImportResult()

    from .registry import is_protected

    # Get insert order — parents first, children last
    all_model_keys = [k for k in backup_data.keys() if not is_protected(*k.split('.'))]
    insert_order = _get_insert_order(all_model_keys)

    for model_key in insert_order:
        if model_key not in backup_data:
            continue
        records = backup_data[model_key]
        try:
            app_label, model_name = model_key.split('.')
            model_class = apps.get_model(app_label, model_name)
        except (LookupError, ValueError) as e:
            result.errors += 1
            result.error_details.append(f'{model_key}: مدل یافت نشد - {str(e)}')
            result.failed_models.append(model_key)
            continue

        try:
            _upsert_records(model_class, records, result)
            result.success_models.append(model_key)
        except Exception as e:
            result.errors += 1
            result.error_details.append(f'{model_key}: {str(e)[:200]}')
            result.failed_models.append(model_key)

    return result


def import_replace_mode(
    backup_data: Dict[str, List[dict]],
    result: Optional[ImportResult] = None,
) -> ImportResult:
    """
    Import data in replace mode.
    Deletes existing data, then inserts backup data.
    Uses savepoints per model for fault tolerance.
    """
    if result is None:
        result = ImportResult()

    from .registry import is_protected

    # Collect models to process
    models_to_process = []
    for model_key in backup_data.keys():
        try:
            app_label, model_name = model_key.split('.')
            if is_protected(app_label, model_name):
                continue
            model_class = apps.get_model(app_label, model_name)
            models_to_process.append((model_key, model_class))
        except (LookupError, ValueError):
            continue

    # Get dependency orders
    model_keys = [mk for mk, _ in models_to_process]
    delete_order = _get_dependency_order(model_keys)  # children first
    insert_order = _get_insert_order(model_keys)      # parents first
    key_to_class = {mk: mc for mk, mc in models_to_process}

    # Phase 1: Delete (children first)
    for model_key in delete_order:
        if model_key not in key_to_class:
            continue
        model_class = key_to_class[model_key]
        sid = transaction.savepoint()
        try:
            count = model_class.objects.count()
            if count > 0:
                model_class.objects.all().delete()
            result.deleted += count
        except Exception as e:
            transaction.savepoint_rollback(sid)
            result.errors += 1
            result.error_details.append(f'{model_key}: خطا در حذف - {str(e)[:200]}')
            result.failed_models.append(model_key)

    # Phase 2: Insert (parents first)
    for model_key in insert_order:
        if model_key not in backup_data:
            continue
        records = backup_data[model_key]
        try:
            model_class = key_to_class.get(model_key)
            if not model_class:
                app_label, model_name = model_key.split('.')
                model_class = apps.get_model(app_label, model_name)
            _bulk_insert(model_class, records, result)
            if model_key not in result.failed_models:
                result.success_models.append(model_key)
        except Exception as e:
            result.errors += 1
            result.error_details.append(f'{model_key}: {str(e)[:200]}')
            if model_key not in result.failed_models:
                result.failed_models.append(model_key)

    return result


def _upsert_records(model_class: type, records: List[dict], result: ImportResult):
    """Insert or update records one by one."""
    # Get concrete field names (includes category_id for FK fields)
    model_fields = set()
    for field in model_class._meta.fields:
        model_fields.add(field.name)
        # Also add the _id version for ForeignKey fields
        if hasattr(field, 'column'):
            model_fields.add(field.column)

    for record in records:
        try:
            record_id = record.get('id')
            clean = {k: v for k, v in record.items() if k in model_fields}

            if record_id is None:
                model_class.objects.create(**clean)
                result.imported += 1
            else:
                existing = model_class.objects.filter(id=record_id).first()
                if existing:
                    for key, value in clean.items():
                        if key != 'id':
                            setattr(existing, key, value)
                    existing.save()
                    result.updated += 1
                else:
                    model_class.objects.create(**clean)
                    result.imported += 1
        except Exception as e:
            result.errors += 1
            result.error_details.append(f'{model_class.__name__} id={record.get("id")}: {str(e)[:200]}')


def _bulk_insert(model_class: type, records: List[dict], result: ImportResult):
    """Bulk insert records for better performance."""
    if not records:
        return

    # Get concrete field names (includes category_id for FK fields)
    model_fields = set()
    for field in model_class._meta.fields:
        model_fields.add(field.name)
        if hasattr(field, 'column'):
            model_fields.add(field.column)

    clean_records = []
    for record in records:
        clean = {k: v for k, v in record.items() if k in model_fields}
        clean_records.append(clean)

    if clean_records:
        objects = [model_class(**record) for record in clean_records]
        model_class.objects.bulk_create(objects, batch_size=500)
        result.imported += len(objects)

"""
Model registry for backup system.
Defines which models are included in backups, organized by sections.
"""
from typing import Dict, List, Type
from django.db.models import Model


# Backup sections - each section groups related models
BACKUP_SECTIONS: Dict[str, dict] = {
    'materials': {
        'label': 'مواد اولیه',
        'icon': 'fas fa-cubes',
        'models': [
            ('materials', 'MaterialCategory'),
            ('materials', 'Material'),
            ('materials', 'MaterialPriceHistory'),
        ],
    },
    'products': {
        'label': 'محصولات',
        'icon': 'fas fa-box',
        'models': [
            ('products', 'Product'),
            ('products', 'ProductMaterial'),
        ],
    },
    'production': {
        'label': 'تولید',
        'icon': 'fas fa-industry',
        'models': [
            ('production', 'ProductionOrder'),
            ('production', 'ProductionMaterial'),
            ('production', 'DailyProduction'),
        ],
    },
    'inventory': {
        'label': 'انبار',
        'icon': 'fas fa-warehouse',
        'models': [
            ('inventory', 'InventoryTransaction'),
            ('inventory', 'PurchaseRecord'),
            ('inventory', 'WasteRecord'),
            ('inventory', 'ReturnRecord'),
            ('inventory', 'ProductInventory'),
            ('inventory', 'ProductInventoryTransaction'),
            ('inventory', 'ProductPurchase'),
        ],
    },
    'workers': {
        'label': 'کارگران',
        'icon': 'fas fa-users',
        'models': [
            ('workers', 'Worker'),
        ],
    },
    'customers': {
        'label': 'مشتریان',
        'icon': 'fas fa-user-tie',
        'models': [
            ('customers', 'Customer'),
        ],
    },
    'invoices': {
        'label': 'فاکتورها',
        'icon': 'fas fa-file-invoice',
        'models': [
            ('invoices', 'Invoice'),
            ('invoices', 'InvoiceItem'),
        ],
    },
    'sms': {
        'label': 'پیامک‌ها',
        'icon': 'fas fa-sms',
        'models': [
            ('sms', 'SmsTemplate'),
            ('sms', 'SmsMessage'),
        ],
    },
    'settings': {
        'label': 'تنظیمات',
        'icon': 'fas fa-cog',
        'models': [
            ('common', 'Setting'),
            ('settings_app', 'FixedCost'),
        ],
    },
    'reports': {
        'label': 'گزارشات',
        'icon': 'fas fa-chart-bar',
        'models': [
            ('updater', 'UpdateLog'),
        ],
    },
}

# Models that should NEVER be deleted during replace mode
PROTECTED_MODELS = {
    ('auth', 'User'),
    ('auth', 'Group'),
    ('auth', 'Permission'),
    ('contenttypes', 'ContentType'),
    ('sessions', 'Session'),
    ('admin', 'LogEntry'),
}

BACKUP_VERSION = '2.0'


def get_all_sections() -> Dict[str, dict]:
    """Return all backup sections."""
    return BACKUP_SECTIONS


def get_section_models(section_key: str) -> List[tuple]:
    """Return model list for a specific section."""
    section = BACKUP_SECTIONS.get(section_key)
    if not section:
        return []
    return section['models']


def get_all_model_keys() -> List[str]:
    """Return all model keys across all sections."""
    keys = []
    for section in BACKUP_SECTIONS.values():
        for app_label, model_name in section['models']:
            keys.append(f'{app_label}.{model_name}')
    return keys


def is_protected(app_label: str, model_name: str) -> bool:
    """Check if a model is protected from deletion."""
    return (app_label, model_name) in PROTECTED_MODELS

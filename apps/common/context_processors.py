from apps.common.models import Setting


THEME_KEYS = {
    'theme_bg_body': '#1e2a3a',
    'theme_bg_card': '#2a3a52',
    'theme_bg_sidebar': '#162033',
    'theme_bg_table_row': '#2a3a52',
    'theme_bg_table_header': 'rgba(99,102,241,0.12)',
    'theme_bg_table_row_hover': '#344a66',
    'theme_text_table': '#e8dcc8',
    'theme_bg_input': '#2a3a52',
    'theme_bg_header': 'rgba(30, 42, 58, 0.85)',
    'theme_accent': '#6366f1',
    'theme_accent_light': '#818cf8',
    'theme_success': '#10b981',
    'theme_danger': '#ef4444',
    'theme_warning': '#f59e0b',
    'theme_info': '#06b6d4',
    'theme_text_primary': '#e8edf5',
    'theme_text_secondary': '#b0bec5',
    'theme_text_muted': '#7e93a8',
    'theme_border': 'rgba(148,163,184,0.08)',
}


def site_context(request):
    theme = {}
    for key, default in THEME_KEYS.items():
        theme[key] = Setting.get_value(key, default)

    theme_css = ';'.join(f'--{k.replace("theme_", "").replace("_", "-")}: {v}' for k, v in theme.items())

    logo_val = Setting.get_value('company_logo', 'fa-industry')
    company_logo_path = '' if logo_val.startswith('fa-') or not logo_val else logo_val

    return {
        'company_name': Setting.get_value('company_name', 'سیستم ERP'),
        'company_info': {
            'name': Setting.get_value('company_name', 'شرکت'),
            'address': Setting.get_value('company_address', ''),
            'phone': Setting.get_value('company_phone', ''),
            'logo': logo_val,
        },
        'company_logo_path': company_logo_path,
        'currency': Setting.get_value('currency', 'ریال'),
        'theme_css': theme_css,
        'theme_data': theme,
    }

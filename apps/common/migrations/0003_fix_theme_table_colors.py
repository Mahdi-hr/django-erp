from django.db import migrations


THEME_FIXES = {
    'theme_bg_table_row': '#2a3a52',
    'theme_text_table': '#e8dcc8',
    'theme_bg_table_row_hover': '#344a66',
}


def fix_theme_table_colors(apps, schema_editor):
    Setting = apps.get_model('common', 'Setting')
    for key, value in THEME_FIXES.items():
        obj, created = Setting.objects.get_or_create(
            key=key,
            defaults={'value': value, 'category': 'theme'},
        )
        if not created:
            # Only overwrite if the stored value is the wrong light color
            if key == 'theme_bg_table_row' and obj.value.lower() in ('#e1eaf7', '#e1eaf7', '#e1eaf7'):
                obj.value = value
                obj.save(update_fields=['value'])


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(fix_theme_table_colors, reverse_fix),
    ]

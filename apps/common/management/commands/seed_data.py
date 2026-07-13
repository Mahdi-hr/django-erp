from django.core.management.base import BaseCommand
from apps.common.models import Setting


class Command(BaseCommand):
    help = 'ایجاد داده‌های اولیه سیستم'

    def handle(self, *args, **options):
        settings_data = [
            ('company_name', 'شرکت تولیدی صنعتی', 'general', 'نام شرکت'),
            ('currency', 'ریال', 'general', 'واحد پول'),
            ('tax_rate', '9', 'financial', 'درصد مالیات'),
            ('water_cost', '50000000', 'financial', 'هزینه آب ماهانه (ریال)'),
            ('electricity_cost', '100000000', 'financial', 'هزینه برق ماهانه (ریال)'),
            ('gas_cost', '30000000', 'financial', 'هزینه گاز ماهانه (ریال)'),
            ('wholesale_multiplier', '0.85', 'financial', 'ضریب قیمت عمده'),
            ('retail_multiplier', '1.1', 'financial', 'ضریب قیمت جزئی'),
            ('dealer_multiplier', '0.90', 'financial', 'ضریب قیمت نمایندگی'),
            ('export_multiplier', '1.15', 'financial', 'ضریب قیمت صادراتی'),
            ('special_multiplier', '0.80', 'financial', 'ضریب قیمت ویژه'),
            ('monthly_units', '1000', 'production', 'تعداد تولید ماهانه'),
        ]

        for key, value, category, description in settings_data:
            Setting.objects.update_or_create(
                key=key,
                defaults={
                    'value': value,
                    'category': category,
                    'description': description,
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Created setting: {key}'))

        self.stdout.write(self.style.SUCCESS('Initial data created successfully'))

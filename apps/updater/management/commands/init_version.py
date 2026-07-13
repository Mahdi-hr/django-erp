import json
from django.core.management.base import BaseCommand
from apps.updater.models import VersionManager


class Command(BaseCommand):
    help = 'مقداردهی اولیه فایل ورژن'

    def add_arguments(self, parser):
        parser.add_argument(
            '--version',
            type=str,
            default='1.0.0',
            help='ورژن اولیه (پیش‌فرض: 1.0.0)'
        )

    def handle(self, *args, **options):
        version = options['version']
        
        if VersionManager.VERSION_FILE.exists():
            self.stdout.write(
                self.style.WARNING(f'فایل ورژن از قبل وجود دارد: {VersionManager.get_current_version()}')
            )
            return

        VersionManager.update_version(version, 'نسخه اولیه')
        self.stdout.write(
            self.style.SUCCESS(f'فایل ورژن با موفقیت ایجاد شد: {version}')
        )

# Generated manually
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backup_type', models.CharField(choices=[('full_backup', 'بکاپ کامل'), ('partial_backup', 'بکاپ جزئی'), ('restore_update', 'بازیابی (بروزرسانی)'), ('restore_replace', 'بازیابی (جایگزینی)')], max_length=20, verbose_name='نوع عملیات')),
                ('status', models.CharField(choices=[('success', 'موفق'), ('failed', 'ناموفق'), ('partial', 'جزئی')], max_length=10, verbose_name='وضعیت')),
                ('filename', models.CharField(blank=True, default='', max_length=255, verbose_name='نام فایل')),
                ('file_size', models.BigIntegerField(default=0, verbose_name='حجم فایل (بایت)')),
                ('record_count', models.PositiveIntegerField(default=0, verbose_name='تعداد رکوردها')),
                ('imported_count', models.PositiveIntegerField(default=0, verbose_name='تعداد رکورد وارد شده')),
                ('updated_count', models.PositiveIntegerField(default=0, verbose_name='تعداد رکورد بروزرسانی شده')),
                ('deleted_count', models.PositiveIntegerField(default=0, verbose_name='تعداد رکورد حذف شده')),
                ('error_count', models.PositiveIntegerField(default=0, verbose_name='تعداد خطاها')),
                ('errors_detail', models.TextField(blank=True, default='', verbose_name='جزئیات خطاها')),
                ('backup_version', models.CharField(default='1.0', max_length=20, verbose_name='نسخه بکاپ')),
                ('metadata_json', models.TextField(blank=True, default='{}', verbose_name='متادیتا')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='ایجادکننده')),
            ],
            options={
                'verbose_name': 'لاگ بکاپ',
                'verbose_name_plural': 'لاگ‌های بکاپ',
                'ordering': ['-created_at'],
            },
        ),
    ]

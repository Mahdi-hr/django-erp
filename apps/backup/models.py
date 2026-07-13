from django.db import models
from django.conf import settings


class BackupLog(models.Model):
    """Tracks all backup and restore operations."""

    TYPE_CHOICES = [
        ('full_backup', 'بکاپ کامل'),
        ('partial_backup', 'بکاپ جزئی'),
        ('restore_update', 'بازیابی (بروزرسانی)'),
        ('restore_replace', 'بازیابی (جایگزینی)'),
    ]
    STATUS_CHOICES = [
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('partial', 'جزئی'),
    ]

    backup_type = models.CharField('نوع عملیات', max_length=20, choices=TYPE_CHOICES)
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES)
    filename = models.CharField('نام فایل', max_length=255, blank=True, default='')
    file_size = models.BigIntegerField('حجم فایل (بایت)', default=0)
    record_count = models.PositiveIntegerField('تعداد رکوردها', default=0)
    imported_count = models.PositiveIntegerField('تعداد رکورد وارد شده', default=0)
    updated_count = models.PositiveIntegerField('تعداد رکورد بروزرسانی شده', default=0)
    deleted_count = models.PositiveIntegerField('تعداد رکورد حذف شده', default=0)
    error_count = models.PositiveIntegerField('تعداد خطاها', default=0)
    errors_detail = models.TextField('جزئیات خطاها', blank=True, default='')
    backup_version = models.CharField('نسخه بکاپ', max_length=20, default='1.0')
    metadata_json = models.TextField('متادیتا', blank=True, default='{}')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name='ایجادکننده'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'لاگ بکاپ'
        verbose_name_plural = 'لاگ‌های بکاپ'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_backup_type_display()} - {self.created_at}'

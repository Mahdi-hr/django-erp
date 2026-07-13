from django.db import models
from django.conf import settings


class Setting(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'عمومی'),
        ('financial', 'مالی'),
        ('inventory', 'انبار'),
        ('production', 'تولید'),
    ]
    key = models.CharField('کلید', max_length=100, unique=True)
    value = models.TextField('مقدار', blank=True, default='')
    category = models.CharField('دسته‌بندی', max_length=20, choices=CATEGORY_CHOICES, default='general')
    description = models.TextField('توضیحات', blank=True, default='')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تنظیم'
        verbose_name_plural = 'تنظیمات'
        ordering = ['category', 'key']

    def __str__(self):
        return f'{self.key}: {self.value}'

    @classmethod
    def get_value(cls, key, default=''):
        try:
            return cls.objects.get(key=key, is_active=True).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, category='general', description=''):
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'category': category, 'description': description}
        )
        return obj


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'اطلاعات'),
        ('warning', 'هشدار'),
        ('error', 'خطا'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name='کاربر')
    title = models.CharField('عنوان', max_length=200)
    message = models.TextField('پیام')
    type = models.CharField('نوع', max_length=10, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField('خوانده شده', default=False)
    reference_type = models.CharField('نوع مرجع', max_length=50, blank=True, default='')
    reference_id = models.PositiveIntegerField('شناسه مرجع', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلانات'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

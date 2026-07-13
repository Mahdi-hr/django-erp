from django.db import models
from django.conf import settings


class SMSTemplate(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'عمومی'),
        ('discount', 'تخفیف'),
        ('new_product', 'محصول جدید'),
        ('order', 'سفارش'),
        ('payment', 'پرداخت'),
        ('holiday', 'تعطیلات'),
        ('birthday', 'تولد'),
        ('promotion', 'تبلیغاتی'),
    ]
    name = models.CharField('نام', max_length=100)
    title = models.CharField('عنوان', max_length=200)
    body = models.TextField('متن پیامک')
    category = models.CharField('دسته‌بندی', max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قالب پیامک'
        verbose_name_plural = 'قالب‌های پیامک'
        ordering = ['name']

    def __str__(self):
        return self.name

    def render(self, **kwargs):
        body = self.body
        for key, value in kwargs.items():
            body = body.replace(f'{{{key}}}', str(value))
        return body


class SMSProviderConfig(models.Model):
    PROVIDER_CHOICES = [
        ('kavenegar', 'کاوه‌نگار'),
        ('smsir', 'SMS.ir'),
    ]
    provider = models.CharField('ارائه‌دهنده', max_length=20, choices=PROVIDER_CHOICES, unique=True)
    api_key = models.CharField('کلید API', max_length=200)
    sender_number = models.CharField('شماره فرستنده', max_length=15)
    is_active = models.BooleanField('فعال', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تنظیمات ارائه‌دهنده پیامک'
        verbose_name_plural = 'تنظیمات ارائه‌دهندگان پیامک'

    def __str__(self):
        return f'{self.get_provider_display()}'


class SMSMessage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('sent', 'ارسال شده'),
        ('failed', 'ناموفق'),
    ]
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مشتری')
    template = models.ForeignKey(SMSTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='قالب')
    phone = models.CharField('شماره تلفن', max_length=15)
    message = models.TextField('متن پیام')
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES, default='pending')
    provider = models.CharField('ارائه‌دهنده', max_length=20, default='demo')
    provider_message_id = models.CharField('شناسه پیام ارائه‌دهنده', max_length=100, blank=True, default='')
    error_message = models.TextField('پیام خطا', blank=True, default='')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ارسال کننده')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پیامک'
        verbose_name_plural = 'پیامک‌ها'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.phone} - {self.status}'

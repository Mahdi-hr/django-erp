from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'مدیر سیستم'),
        ('accountant', 'حسابدار'),
        ('warehouse', 'انباردار'),
        ('operator', 'اپراتور'),
        ('viewer', 'مشاهده‌گر'),
    ]
    full_name = models.CharField('نام کامل', max_length=200, blank=True, default='')
    role = models.CharField('نقش', max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField('تلفن', max_length=15, blank=True, default='')
    is_active = models.BooleanField('فعال', default=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='گروه‌ها',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='erp_user_set',
        related_query_name='erp_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='مجوزهای کاربر',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='erp_user_set',
        related_query_name='erp_user',
    )

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.get_full_name() or self.username

    def has_permission(self, permission):
        permissions = {
            'admin': ['all'],
            'accountant': ['view_reports', 'manage_invoices', 'view_materials', 'view_products'],
            'warehouse': ['manage_inventory', 'manage_materials', 'manage_purchases', 'manage_waste'],
            'operator': ['register_daily_production', 'view_orders'],
            'viewer': ['view_only'],
        }
        role_perms = permissions.get(self.role, [])
        return 'all' in role_perms or permission in role_perms


class AuditLog(models.Model):
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, verbose_name='کاربر')
    action = models.CharField('عملیات', max_length=50)
    entity_type = models.CharField('نوع موجودیت', max_length=50)
    entity_id = models.PositiveIntegerField('شناسه موجودیت', null=True, blank=True)
    old_value = models.TextField('مقدار قبلی', blank=True, default='')
    new_value = models.TextField('مقدار جدید', blank=True, default='')
    ip_address = models.GenericIPAddressField('آدرس IP', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'گزارش فعالیت'
        verbose_name_plural = 'گزارش‌های فعالیت'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.action} - {self.entity_type}'

from django.db import models
from django.conf import settings


class MaterialCategory(models.Model):
    name = models.CharField('نام', max_length=200)
    description = models.TextField('توضیحات', blank=True, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='دسته والد')
    sort_order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'دسته‌بندی مواد اولیه'
        verbose_name_plural = 'دسته‌بندی مواد اولیه'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Material(models.Model):
    UNIT_CHOICES = [
        ('kg', 'کیلوگرم'),
        ('piece', 'عدد'),
        ('unit', 'واحد'),
        ('meter', 'متر'),
        ('liter', 'لیتر'),
        ('roll', 'گرم'),
    ]
    name = models.CharField('نام', max_length=200)
    category = models.ForeignKey(MaterialCategory, on_delete=models.PROTECT, related_name='materials', verbose_name='دسته‌بندی')
    unit = models.CharField('واحد', max_length=10, choices=UNIT_CHOICES, default='kg')
    purchase_price = models.DecimalField('قیمت خرید', max_digits=15, decimal_places=0, default=0)
    purchase_date = models.DateField('تاریخ خرید', null=True, blank=True)
    supplier = models.CharField('تامین‌کننده', max_length=200, blank=True, default='')
    code = models.CharField('کد', max_length=50, unique=True)
    barcode = models.CharField('بارکد', max_length=100, blank=True, default='')
    qr_code = models.CharField('QR Code', max_length=200, blank=True, default='')
    min_stock = models.DecimalField('حداقل موجودی', max_digits=15, decimal_places=2, default=0)
    current_stock = models.DecimalField('موجودی فعلی', max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField('فعال', default=True)
    description = models.TextField('توضیحات', blank=True, default='')
    image = models.ImageField('تصویر', upload_to='materials/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ماده اولیه'
        verbose_name_plural = 'مواد اولیه'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f'{self.name} ({self.code})'

    @property
    def is_low_stock(self):
        return self.current_stock < self.min_stock

    @property
    def stock_status(self):
        from apps.common.models import Setting
        out_of_stock_threshold = int(Setting.get_value('out_of_stock_threshold', '0'))
        low_stock_threshold = int(Setting.get_value('low_stock_threshold', '10'))
        if self.current_stock <= out_of_stock_threshold:
            return 'out_of_stock'
        elif self.current_stock <= low_stock_threshold:
            return 'low'
        return 'sufficient'

    def get_unit_display_fa(self):
        return dict(self.UNIT_CHOICES).get(self.unit, self.unit)


class MaterialPriceHistory(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='price_history', verbose_name='ماده اولیه')
    old_price = models.DecimalField('قیمت قبلی', max_digits=15, decimal_places=0)
    new_price = models.DecimalField('قیمت جدید', max_digits=15, decimal_places=0)
    change_date = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='تغییردهنده')
    reason = models.TextField('دلیل تغییر', blank=True, default='')

    class Meta:
        verbose_name = 'تاریخچه قیمت ماده'
        verbose_name_plural = 'تاریخچه قیمت مواد'
        ordering = ['-change_date']

    def __str__(self):
        return f'{self.material.name}: {self.old_price} -> {self.new_price}'

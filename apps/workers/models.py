from django.db import models


class Worker(models.Model):
    ROLE_CHOICES = [
        ('welder', 'جوشکار'),
        ('assembler', 'مونتاژکار'),
        ('painter', 'رنگ‌کار'),
        ('packer', 'بسته‌بند'),
        ('operator', 'اپراتور'),
        ('other', 'سایر'),
    ]
    name = models.CharField('نام', max_length=200)
    phone = models.CharField('تلفن', max_length=15, blank=True, default='')
    role = models.CharField('نقش', max_length=20, choices=ROLE_CHOICES, default='other')
    is_active = models.BooleanField('فعال', default=True)
    # Fields for worker edit page
    national_id = models.CharField('کد ملی', max_length=10, blank=True, default='')
    address = models.TextField('آدرس', blank=True, default='')
    birth_date = models.DateField('تاریخ تولد', null=True, blank=True)
    hire_date = models.DateField('تاریخ استخدام', null=True, blank=True)
    skill = models.CharField('مهارت اصلی', max_length=200, blank=True, default='')
    experience_years = models.PositiveIntegerField('سال‌های تجربه', default=0)
    salary = models.DecimalField('حقوق (ریال)', max_digits=15, decimal_places=0, default=0)
    insurance_number = models.CharField('شماره بیمه', max_length=20, blank=True, default='')
    emergency_phone = models.CharField('تلفن اضطراری', max_length=15, blank=True, default='')
    description = models.TextField('توضیحات', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'کارگر'
        verbose_name_plural = 'کارگران'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_role_display_fa(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    @property
    def total_products_made(self):
        from apps.production.models import DailyProduction
        return DailyProduction.objects.filter(worker=self, status='completed').aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def production_count(self):
        from apps.production.models import DailyProduction
        return DailyProduction.objects.filter(worker=self, status='completed').count()

    @property
    def products_list(self):
        from apps.production.models import DailyProduction
        from django.db.models import Sum
        return DailyProduction.objects.filter(
            worker=self, status='completed'
        ).values('product__name', 'product__code').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')

    @property
    def first_production_date(self):
        from apps.production.models import DailyProduction
        dp = DailyProduction.objects.filter(worker=self).order_by('production_date').first()
        return dp.production_date if dp else None

    @property
    def last_production_date(self):
        from apps.production.models import DailyProduction
        dp = DailyProduction.objects.filter(worker=self).order_by('-production_date').first()
        return dp.production_date if dp else None

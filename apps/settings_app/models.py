from django.db import models


class FixedCost(models.Model):
    name = models.CharField('نام هزینه', max_length=200)
    amount = models.DecimalField('مبلغ (ریال)', max_digits=15, decimal_places=0)
    category = models.CharField('دسته‌بندی', max_length=50, blank=True, default='')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'هزینه ثابت'
        verbose_name_plural = 'هزینه‌های ثابت'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}: {self.amount}'

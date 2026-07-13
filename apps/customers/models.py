from django.db import models


class Customer(models.Model):
    name = models.CharField('نام', max_length=200)
    company = models.CharField('شرکت', max_length=200, blank=True, default='')
    phone = models.CharField('تلفن', max_length=15, blank=True, default='')
    email = models.EmailField('ایمیل', blank=True, default='')
    address = models.TextField('آدرس', blank=True, default='')
    city = models.CharField('شهر', max_length=100, blank=True, default='')
    tax_number = models.CharField('شماره مالیاتی', max_length=20, blank=True, default='')
    national_id = models.CharField('کد ملی', max_length=10, blank=True, default='')
    balance = models.DecimalField('مانده حساب', max_digits=15, decimal_places=0, default=0)
    credit_limit = models.DecimalField('حد اعتبار', max_digits=15, decimal_places=0, default=0)
    discount_percent = models.DecimalField('درصد تخفیف', max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField('فعال', default=True)
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مشتری'
        verbose_name_plural = 'مشتریان'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.company})' if self.company else self.name

    @property
    def total_debt(self):
        """مجموع باقیمانده تمام فاکتورهای فروش"""
        from apps.invoices.models import Invoice
        invoices = Invoice.objects.filter(customer=self, type='sale')
        return sum(
            int(inv.total) - int(inv.paid_amount)
            for inv in invoices
            if int(inv.total) > int(inv.paid_amount)
        )

    @property
    def is_debtor(self):
        return self.total_debt > 0

    @property
    def is_creditor(self):
        return self.total_debt < 0

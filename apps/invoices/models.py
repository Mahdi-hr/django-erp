from django.db import models
from django.conf import settings
from django.utils import timezone


class Invoice(models.Model):
    TYPE_CHOICES = [
        ('sale', 'فاکتور فروش'),
        ('return', 'برگشت از فروش'),
        ('proforma', 'پیش‌فاکتور'),
        ('official', 'فاکتور رسمی'),
        ('credit', 'اعتباری'),
        ('cash', 'نقدی'),
    ]
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('sent', 'ارسال شده'),
        ('paid', 'پرداخت شده'),
        ('partial', 'پرداخت جزئی'),
        ('cancelled', 'لغو شده'),
    ]
    invoice_number = models.CharField('شماره فاکتور', max_length=20, unique=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='invoices', verbose_name='مشتری')
    type = models.CharField('نوع', max_length=10, choices=TYPE_CHOICES, default='sale')
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField('تاریخ صدور')
    subtotal = models.DecimalField('جمع کل', max_digits=15, decimal_places=0, default=0)
    discount_amount = models.DecimalField('مبلغ تخفیف', max_digits=15, decimal_places=0, default=0)
    tax_amount = models.DecimalField('مبلغ مالیات', max_digits=15, decimal_places=0, default=0)
    total = models.DecimalField('مبلغ کل', max_digits=15, decimal_places=0, default=0)
    paid_amount = models.DecimalField('مبلغ پرداختی', max_digits=15, decimal_places=0, default=0)
    remaining_amount = models.DecimalField('مبلغ باقیمانده', max_digits=15, decimal_places=0, default=0)
    payment_method = models.CharField('روش پرداخت', max_length=50, blank=True, default='')
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    deduct_stock = models.BooleanField('کم شدن از انبار', default=True, help_text='آیا از موجودی انبار کم شود؟')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.invoice_number} - {self.customer.name}'

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.now().year
            last = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{year}'
            ).order_by('-invoice_number').first()
            if last:
                num = int(last.invoice_number.split('-')[-1]) + 1
            else:
                num = 1
            self.invoice_number = f'INV-{year}-{num:05d}'
        super().save(*args, **kwargs)

    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items.all())
        from apps.common.models import Setting
        tax_percent = int(Setting.get_value('tax_rate', '10'))
        self.tax_amount = int(self.subtotal * tax_percent / 100)
        self.total = self.subtotal - self.discount_amount + self.tax_amount
        self.remaining_amount = self.total - self.paid_amount
        if self.paid_amount <= 0:
            self.status = 'draft'
        elif self.remaining_amount <= 0:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.save(update_fields=[
            'subtotal', 'tax_amount', 'total', 'remaining_amount', 'status'
        ])

    def apply_product_inventory(self):
        if not self.deduct_stock:
            return
        from apps.inventory.models import ProductInventory, ProductInventoryTransaction
        for item in self.items.filter(product__isnull=False):
            if item.product:
                pi, _ = ProductInventory.objects.get_or_create(product=item.product)
                pi.current_stock -= item.quantity
                pi.save(update_fields=['current_stock'])
                ProductInventoryTransaction.objects.create(
                    product=item.product,
                    type='sale',
                    quantity=item.quantity,
                    reference_type='invoice',
                    reference_id=self.pk,
                    notes=f'فروش در فاکتور {self.invoice_number}',
                    created_by=self.created_by,
                )

    def reverse_product_inventory(self):
        if not self.deduct_stock:
            return
        from apps.inventory.models import ProductInventory, ProductInventoryTransaction
        for item in self.items.filter(product__isnull=False):
            if item.product:
                pi, _ = ProductInventory.objects.get_or_create(product=item.product)
                pi.current_stock += item.quantity
                pi.save(update_fields=['current_stock'])
                ProductInventoryTransaction.objects.filter(
                    reference_type='invoice',
                    reference_id=self.pk,
                    product=item.product,
                ).delete()

    def check_stock_availability(self):
        from apps.inventory.models import ProductInventory
        errors = []
        if not self.deduct_stock:
            return errors
        for item in self.items.filter(product__isnull=False):
            if item.product:
                pi, _ = ProductInventory.objects.get_or_create(product=item.product)
                if pi.current_stock < item.quantity:
                    errors.append({
                        'product': item.product.name,
                        'requested': item.quantity,
                        'available': pi.current_stock,
                    })
        return errors

    def register_payment(self, amount, method=''):
        self.paid_amount += amount
        self.remaining_amount = self.total - self.paid_amount
        if self.remaining_amount <= 0:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.payment_method = method
        self.save(update_fields=[
            'paid_amount', 'remaining_amount', 'status', 'payment_method'
        ])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='فاکتور')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='محصول')
    description = models.CharField('توضیحات', max_length=300)
    quantity = models.PositiveIntegerField('تعداد', default=1)
    unit_price = models.DecimalField('قیمت هر واحد', max_digits=15, decimal_places=0)
    discount_percent = models.DecimalField('درصد تخفیف', max_digits=5, decimal_places=2, default=0)
    tax_percent = models.DecimalField('درصد مالیات', max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField('جمع', max_digits=15, decimal_places=0, default=0)

    class Meta:
        verbose_name = 'قلم فاکتور'
        verbose_name_plural = 'اقلام فاکتور'

    def __str__(self):
        return f'{self.description} x {self.quantity}'

    def calculate_total(self):
        base = self.unit_price * self.quantity
        discount = base * self.discount_percent / 100
        tax = (base - discount) * self.tax_percent / 100
        self.total = base - discount + tax
        return self.total

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)

from django.db import models
from django.conf import settings


class InventoryTransaction(models.Model):
    TYPE_CHOICES = [
        ('in', 'ورود'),
        ('out', 'خروج'),
        ('adjust', 'اصلاح'),
        ('waste', 'ضایعات'),
        ('return', 'برگشت'),
    ]
    material = models.ForeignKey('materials.Material', on_delete=models.PROTECT, related_name='transactions', verbose_name='ماده اولیه')
    type = models.CharField('نوع تراکنش', max_length=10, choices=TYPE_CHOICES)
    quantity = models.DecimalField('مقدار', max_digits=15, decimal_places=4)
    unit_price = models.DecimalField('قیمت هر واحد', max_digits=15, decimal_places=0, default=0)
    total_price = models.DecimalField('قیمت کل', max_digits=15, decimal_places=0, default=0)
    reference_type = models.CharField('نوع مرجع', max_length=50, blank=True, default='')
    reference_id = models.PositiveIntegerField('شناسه مرجع', null=True, blank=True)
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    transaction_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')

    class Meta:
        verbose_name = 'تراکنش انبار'
        verbose_name_plural = 'تراکنش‌های انبار'
        ordering = ['-transaction_date']

    def __str__(self):
        return f'{self.get_type_display()} - {self.material.name}: {self.quantity}'


class PurchaseRecord(models.Model):
    material = models.ForeignKey('materials.Material', on_delete=models.PROTECT, related_name='purchases', verbose_name='ماده اولیه')
    quantity = models.DecimalField('مقدار', max_digits=15, decimal_places=4)
    unit_price = models.DecimalField('قیمت هر واحد', max_digits=15, decimal_places=0)
    total_price = models.DecimalField('قیمت کل', max_digits=15, decimal_places=0)
    supplier = models.CharField('تامین‌کننده', max_length=200)
    invoice_number = models.CharField('شماره فاکتور', max_length=100, blank=True, default='')
    purchase_date = models.DateField('تاریخ خرید')
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'رکورد خرید'
        verbose_name_plural = 'رکوردهای خرید'
        ordering = ['-purchase_date']

    def __str__(self):
        return f'{self.material.name} - {self.supplier} ({self.purchase_date})'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.material.current_stock += self.quantity
        self.material.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(
            material=self.material,
            type='in',
            quantity=self.quantity,
            unit_price=self.unit_price,
            total_price=self.total_price,
            reference_type='purchase',
            reference_id=self.pk,
            notes=f'خرید از {self.supplier}',
            created_by=self.created_by,
        )
        if self.material.purchase_price != self.unit_price:
            from apps.materials.models import MaterialPriceHistory
            MaterialPriceHistory.objects.create(
                material=self.material,
                old_price=self.material.purchase_price,
                new_price=self.unit_price,
                changed_by=self.created_by,
                reason=f'خرید با قیمت جدید از {self.supplier}',
            )
            self.material.purchase_price = self.unit_price
            self.material.save(update_fields=['purchase_price'])


class WasteRecord(models.Model):
    material = models.ForeignKey('materials.Material', on_delete=models.PROTECT, related_name='waste_records', verbose_name='ماده اولیه')
    quantity = models.DecimalField('مقدار', max_digits=15, decimal_places=4)
    reason = models.TextField('دلیل')
    production_order = models.ForeignKey('production.ProductionOrder', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='سفارش تولید')
    waste_date = models.DateField('تاریخ ضایعات')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'رکورد ضایعات'
        verbose_name_plural = 'رکوردهای ضایعات'
        ordering = ['-waste_date']

    def __str__(self):
        return f'{self.material.name} - {self.quantity} ({self.waste_date})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.material.current_stock -= self.quantity
        if self.material.current_stock < 0:
            self.material.current_stock = 0
        self.material.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(
            material=self.material,
            type='waste',
            quantity=self.quantity,
            unit_price=self.material.purchase_price,
            total_price=self.quantity * self.material.purchase_price,
            reference_type='waste',
            reference_id=self.pk,
            notes=f'ضایعات: {self.reason}',
            created_by=self.created_by,
        )


class ReturnRecord(models.Model):
    material = models.ForeignKey('materials.Material', on_delete=models.PROTECT, related_name='return_records', verbose_name='ماده اولیه')
    quantity = models.DecimalField('مقدار', max_digits=15, decimal_places=4)
    reason = models.TextField('دلیل')
    source = models.CharField('منبع برگشت', max_length=200)
    return_date = models.DateField('تاریخ برگشت')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'رکورد برگشت'
        verbose_name_plural = 'رکوردهای برگشت'
        ordering = ['-return_date']

    def __str__(self):
        return f'{self.material.name} - {self.quantity} ({self.return_date})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.material.current_stock += self.quantity
        self.material.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(
            material=self.material,
            type='return',
            quantity=self.quantity,
            unit_price=self.material.purchase_price,
            total_price=self.quantity * self.material.purchase_price,
            reference_type='return',
            reference_id=self.pk,
            notes=f'برگشت از {self.source}: {self.reason}',
            created_by=self.created_by,
        )


class ProductInventory(models.Model):
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, related_name='inventory', verbose_name='محصول')
    current_stock = models.IntegerField('موجودی فعلی', default=0)
    min_stock = models.PositiveIntegerField('حداقل موجودی', default=0)
    last_production_date = models.DateField('آخرین تاریخ تولید', null=True, blank=True)

    class Meta:
        verbose_name = 'موجودی محصول'
        verbose_name_plural = 'موجودی محصولات'

    def __str__(self):
        return f'{self.product.name}: {self.current_stock}'

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


class ProductPurchase(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='purchases', verbose_name='محصول')
    quantity = models.PositiveIntegerField('مقدار')
    unit_price = models.DecimalField('قیمت هر واحد', max_digits=15, decimal_places=0)
    total_price = models.DecimalField('قیمت کل', max_digits=15, decimal_places=0)
    supplier = models.CharField('تامین‌کننده', max_length=200)
    invoice_number = models.CharField('شماره فاکتور', max_length=100, blank=True, default='')
    purchase_date = models.DateField('تاریخ خرید')
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'رکورد خرید محصول'
        verbose_name_plural = 'رکوردهای خرید محصولات'
        ordering = ['-purchase_date']

    def __str__(self):
        return f'{self.product.name} - {self.supplier} ({self.purchase_date})'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        pi, _ = ProductInventory.objects.get_or_create(product=self.product)
        pi.current_stock += self.quantity
        pi.save(update_fields=['current_stock'])
        ProductInventoryTransaction.objects.create(
            product=self.product,
            type='purchase',
            quantity=self.quantity,
            reference_type='product_purchase',
            reference_id=self.pk,
            notes=f'خرید از {self.supplier}',
            created_by=self.created_by,
        )


class ProductInventoryTransaction(models.Model):
    TYPE_CHOICES = [
        ('production', 'تولید'),
        ('sale', 'فروش'),
        ('purchase', 'خرید'),
        ('return', 'برگشت'),
        ('adjust', 'اصلاح'),
        ('waste', 'ضایعات'),
    ]
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='inventory_transactions', verbose_name='محصول')
    type = models.CharField('نوع تراکنش', max_length=10, choices=TYPE_CHOICES)
    quantity = models.IntegerField('مقدار')
    reference_type = models.CharField('نوع مرجع', max_length=50, blank=True, default='')
    reference_id = models.PositiveIntegerField('شناسه مرجع', null=True, blank=True)
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تراکنش موجودی محصول'
        verbose_name_plural = 'تراکنش‌های موجودی محصولات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} - {self.get_type_display()}: {self.quantity}'

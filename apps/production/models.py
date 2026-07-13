from django.db import models
from django.conf import settings


class ProductionOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال تولید'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
    ]
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='production_orders', verbose_name='محصول')
    quantity = models.PositiveIntegerField('تعداد')
    unit_cost = models.DecimalField('هزینه هر واحد', max_digits=15, decimal_places=0, default=0)
    total_cost = models.DecimalField('هزینه کل', max_digits=15, decimal_places=0, default=0)
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.PositiveIntegerField('اولویت', default=0)
    planned_date = models.DateField('تاریخ برنامه‌ریزی')
    start_date = models.DateField('تاریخ شروع', null=True, blank=True)
    end_date = models.DateField('تاریخ پایان', null=True, blank=True)
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سفارش تولید'
        verbose_name_plural = 'سفارشات تولید'
        ordering = ['-created_at']

    def __str__(self):
        return f'سفارش #{self.pk} - {self.product.name} x {self.quantity}'

    def calculate_costs(self):
        self.unit_cost = self.product.cost_price
        self.total_cost = self.unit_cost * self.quantity
        self.save(update_fields=['unit_cost', 'total_cost'])

    def start_production(self):
        self.status = 'in_progress'
        self.start_date = timezone.now().date()
        self.save(update_fields=['status', 'start_date'])

    def complete_production(self):
        from apps.inventory.models import InventoryTransaction, ProductInventory, ProductInventoryTransaction
        for pm in self.product.materials.all():
            required_qty = pm.quantity * self.quantity
            if pm.material.current_stock < required_qty:
                raise ValueError(f'موجودی ماده {pm.material.name} کافی نیست')
        for pm in self.product.materials.all():
            required_qty = pm.quantity * self.quantity
            pm.material.current_stock -= required_qty
            pm.material.save(update_fields=['current_stock'])
            InventoryTransaction.objects.create(
                material=pm.material,
                type='out',
                quantity=required_qty,
                unit_price=pm.material.purchase_price,
                total_price=required_qty * pm.material.purchase_price,
                reference_type='production_order',
                reference_id=self.pk,
                notes=f'مصرف برای سفارش تولید #{self.pk}',
                created_by=self.created_by,
            )
        pi, _ = ProductInventory.objects.get_or_create(product=self.product)
        pi.current_stock += self.quantity
        pi.save(update_fields=['current_stock'])
        ProductInventoryTransaction.objects.create(
            product=self.product,
            type='production',
            quantity=self.quantity,
            reference_type='production_order',
            reference_id=self.pk,
            notes=f'تولید سفارش #{self.pk}',
            created_by=self.created_by,
        )
        self.status = 'completed'
        self.end_date = timezone.now().date()
        self.save(update_fields=['status', 'end_date'])


from django.utils import timezone


class ProductionMaterial(models.Model):
    order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='materials', verbose_name='سفارش تولید')
    material = models.ForeignKey('materials.Material', on_delete=models.PROTECT, verbose_name='ماده اولیه')
    planned_quantity = models.DecimalField('مقدار برنامه‌ریزی شده', max_digits=15, decimal_places=4)
    actual_quantity = models.DecimalField('مقدار واقعی', max_digits=15, decimal_places=4, null=True, blank=True)
    unit_cost = models.DecimalField('هزینه هر واحد', max_digits=15, decimal_places=0, default=0)
    total_cost = models.DecimalField('هزینه کل', max_digits=15, decimal_places=0, default=0)

    class Meta:
        verbose_name = 'ماده مصرفی سفارش'
        verbose_name_plural = 'مواد مصرفی سفارشات'

    def __str__(self):
        return f'{self.order} - {self.material.name}: {self.planned_quantity}'

    def save(self, *args, **kwargs):
        self.unit_cost = self.material.purchase_price
        self.total_cost = self.unit_cost * self.planned_quantity
        super().save(*args, **kwargs)


class DailyProduction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
    ]
    worker = models.ForeignKey('workers.Worker', on_delete=models.PROTECT, related_name='daily_productions', verbose_name='کارگر')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='daily_productions', verbose_name='محصول')
    quantity = models.PositiveIntegerField('تعداد')
    production_date = models.DateField('تاریخ تولید')
    notes = models.TextField('یادداشت‌ها', blank=True, default='')
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='ایجاد کننده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تولید روزانه'
        verbose_name_plural = 'تولیدات روزانه'
        ordering = ['-production_date']

    def __str__(self):
        return f'{self.worker.name} - {self.product.name} x {self.quantity} ({self.production_date})'

    def apply_inventory(self):
        from apps.inventory.models import InventoryTransaction, ProductInventory, ProductInventoryTransaction
        for pm in self.product.materials.all():
            required_qty = pm.quantity * self.quantity
            if pm.material.current_stock < required_qty:
                raise ValueError(f'موجودی ماده {pm.material.name} کافی نیست')
        for pm in self.product.materials.all():
            required_qty = pm.quantity * self.quantity
            pm.material.current_stock -= required_qty
            pm.material.save(update_fields=['current_stock'])
            InventoryTransaction.objects.create(
                material=pm.material,
                type='out',
                quantity=required_qty,
                unit_price=pm.material.purchase_price,
                total_price=required_qty * pm.material.purchase_price,
                reference_type='daily_production',
                reference_id=self.pk,
                notes=f'تولید روزانه #{self.pk}',
                created_by=self.created_by,
            )
        pi, _ = ProductInventory.objects.get_or_create(product=self.product)
        pi.current_stock += self.quantity
        pi.save(update_fields=['current_stock'])
        ProductInventoryTransaction.objects.create(
            product=self.product,
            type='production',
            quantity=self.quantity,
            reference_type='daily_production',
            reference_id=self.pk,
            notes=f'تولید روزانه #{self.pk}',
            created_by=self.created_by,
        )

    def reverse_inventory(self):
        from apps.inventory.models import InventoryTransaction, ProductInventory, ProductInventoryTransaction
        for pm in self.product.materials.all():
            used_qty = pm.quantity * self.quantity
            pm.material.current_stock += used_qty
            pm.material.save(update_fields=['current_stock'])
            InventoryTransaction.objects.filter(
                reference_type='daily_production',
                reference_id=self.pk,
                material=pm.material,
            ).delete()
        pi, _ = ProductInventory.objects.get_or_create(product=self.product)
        pi.current_stock -= self.quantity
        pi.save(update_fields=['current_stock'])
        ProductInventoryTransaction.objects.filter(
            reference_type='daily_production',
            reference_id=self.pk,
            product=self.product,
        ).delete()

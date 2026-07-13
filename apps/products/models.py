from django.db import models
from django.conf import settings


class Product(models.Model):
    name = models.CharField('نام', max_length=200)
    code = models.CharField('کد', max_length=50, unique=True)
    barcode = models.CharField('بارکد', max_length=100, blank=True, default='')
    qr_code = models.CharField('QR Code', max_length=200, blank=True, default='')
    category = models.CharField('دسته‌بندی', max_length=100, blank=True, default='')
    image = models.ImageField('تصویر', upload_to='products/', blank=True, null=True)
    description = models.TextField('توضیحات', blank=True, default='')
    sale_price = models.DecimalField('قیمت فروش', max_digits=15, decimal_places=0, default=0)
    wholesale_price = models.DecimalField('قیمت عمده', max_digits=15, decimal_places=0, default=0)
    retail_price = models.DecimalField('قیمت جزئی', max_digits=15, decimal_places=0, default=0)
    dealer_price = models.DecimalField('قیمت نمایندگی', max_digits=15, decimal_places=0, default=0)
    export_price = models.DecimalField('قیمت صادراتی', max_digits=15, decimal_places=0, default=0)
    special_price = models.DecimalField('قیمت ویژه', max_digits=15, decimal_places=0, default=0)
    profit_percent = models.DecimalField('درصد سود', max_digits=5, decimal_places=2, default=30)
    fixed_profit = models.DecimalField('سود ثابت (ریال)', max_digits=15, decimal_places=0, null=True, blank=True)
    cost_price = models.DecimalField('قیمت تمام‌شده', max_digits=15, decimal_places=0, default=0)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'

    def calculate_cost_price(self):
        from apps.products.services import calculate_product_cost
        return calculate_product_cost(self)

    def recalculate_prices(self):
        tax_rate = float(self.profit_percent) / 100
        self.sale_price = int(self.cost_price * (1 + tax_rate))
        if self.fixed_profit:
            self.sale_price += int(self.fixed_profit)
        wholesale_mult = float(Setting.get_value('wholesale_multiplier', '0.85'))
        retail_mult = float(Setting.get_value('retail_multiplier', '1.1'))
        dealer_mult = float(Setting.get_value('dealer_multiplier', '0.90'))
        export_mult = float(Setting.get_value('export_multiplier', '1.15'))
        special_mult = float(Setting.get_value('special_multiplier', '0.80'))
        self.wholesale_price = int(self.sale_price * wholesale_mult)
        self.retail_price = int(self.sale_price * retail_mult)
        self.dealer_price = int(self.sale_price * dealer_mult)
        self.export_price = int(self.sale_price * export_mult)
        self.special_price = int(self.sale_price * special_mult)
        self.save(update_fields=[
            'sale_price', 'wholesale_price', 'retail_price',
            'dealer_price', 'export_price', 'special_price'
        ])


from apps.common.models import Setting


class ProductMaterial(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='materials', verbose_name='محصول')
    material = models.ForeignKey('materials.Material', on_delete=models.PROTECT, related_name='product_materials', verbose_name='ماده اولیه')
    quantity = models.DecimalField('مقدار مصرف', max_digits=15, decimal_places=4)
    unit = models.CharField('واحد', max_length=10, default='kg')

    class Meta:
        verbose_name = 'ماده مصرفی محصول (BOM)'
        verbose_name_plural = 'لیست مواد مصرفی محصولات (BOM)'
        unique_together = ('product', 'material')

    def __str__(self):
        return f'{self.product.name} - {self.material.name}: {self.quantity} {self.unit}'

    @property
    def total_cost(self):
        return self.quantity * self.material.purchase_price

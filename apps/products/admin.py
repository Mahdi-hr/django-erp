from django.contrib import admin
from .models import Product, ProductMaterial


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'cost_price', 'sale_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'code', 'barcode']


@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ['product', 'material', 'quantity', 'unit']
    list_filter = ['product']

from django.contrib import admin
from .models import MaterialCategory, Material, MaterialPriceHistory


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'sort_order', 'is_active']
    list_filter = ['is_active']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'purchase_price', 'current_stock', 'is_active']
    list_filter = ['category', 'unit', 'is_active']
    search_fields = ['name', 'code', 'barcode']


@admin.register(MaterialPriceHistory)
class MaterialPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['material', 'old_price', 'new_price', 'changed_by', 'change_date']
    list_filter = ['material']

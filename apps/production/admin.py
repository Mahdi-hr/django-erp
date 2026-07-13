from django.contrib import admin
from .models import ProductionOrder, ProductionMaterial, DailyProduction


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'product', 'quantity', 'status', 'planned_date', 'created_by']
    list_filter = ['status', 'planned_date']
    search_fields = ['product__name']


@admin.register(ProductionMaterial)
class ProductionMaterialAdmin(admin.ModelAdmin):
    list_display = ['order', 'material', 'planned_quantity', 'actual_quantity', 'total_cost']
    list_filter = ['order']


@admin.register(DailyProduction)
class DailyProductionAdmin(admin.ModelAdmin):
    list_display = ['worker', 'product', 'quantity', 'production_date', 'status']
    list_filter = ['status', 'production_date']
    search_fields = ['worker__name', 'product__name']

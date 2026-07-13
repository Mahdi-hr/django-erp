from django.contrib import admin
from .models import InventoryTransaction, PurchaseRecord, WasteRecord, ReturnRecord, ProductInventory, ProductInventoryTransaction, ProductPurchase


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['material', 'type', 'quantity', 'unit_price', 'total_price', 'transaction_date']
    list_filter = ['type', 'material']
    search_fields = ['material__name', 'notes']


@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ['material', 'quantity', 'unit_price', 'total_price', 'supplier', 'purchase_date']
    list_filter = ['purchase_date']
    search_fields = ['supplier', 'material__name']


@admin.register(WasteRecord)
class WasteRecordAdmin(admin.ModelAdmin):
    list_display = ['material', 'quantity', 'reason', 'waste_date']
    list_filter = ['waste_date']
    search_fields = ['material__name', 'reason']


@admin.register(ReturnRecord)
class ReturnRecordAdmin(admin.ModelAdmin):
    list_display = ['material', 'quantity', 'reason', 'source', 'return_date']
    list_filter = ['return_date']
    search_fields = ['material__name', 'source']


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'current_stock', 'min_stock', 'last_production_date']
    search_fields = ['product__name']


@admin.register(ProductInventoryTransaction)
class ProductInventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'type', 'quantity', 'reference_type', 'created_at']
    list_filter = ['type']
    search_fields = ['product__name']


@admin.register(ProductPurchase)
class ProductPurchaseAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'unit_price', 'total_price', 'supplier', 'purchase_date']
    list_filter = ['purchase_date']
    search_fields = ['supplier', 'product__name']

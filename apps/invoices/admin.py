from django.contrib import admin
from .models import Invoice, InvoiceItem


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'type', 'status', 'total', 'paid_amount', 'issue_date']
    list_filter = ['status', 'type', 'issue_date']
    search_fields = ['invoice_number', 'customer__name']


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'description', 'quantity', 'unit_price', 'total']
    list_filter = ['invoice']
    search_fields = ['description', 'product__name']

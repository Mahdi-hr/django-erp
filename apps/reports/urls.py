from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('material-usage/', views.material_usage_report, name='material_usage_report'),
    path('production-cost/', views.production_cost_report, name='production_cost_report'),
    path('profit/', views.profit_report, name='profit_report'),
    path('purchases/', views.purchase_report, name='purchase_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('product-prices/', views.product_price_list, name='product_price_list'),
    path('price-changes/', views.price_change_report, name='price_change_report'),
    path('financial-summary/', views.financial_summary, name='financial_summary'),
    path('invoices/', views.invoice_report, name='invoice_report'),
    path('workers/', views.worker_report, name='worker_report'),
    path('export/<str:report_type>/', views.export_csv, name='export_csv'),
]

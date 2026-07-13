from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone


@login_required
def dashboard(request):
    from apps.materials.models import Material
    from apps.products.models import Product
    from apps.production.models import ProductionOrder, DailyProduction
    from apps.invoices.models import Invoice
    from apps.inventory.models import ProductInventory, PurchaseRecord
    from apps.workers.models import Worker

    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Materials - stock stats
    materials = Material.objects.filter(is_active=True)
    material_low = [m for m in materials if m.stock_status != 'sufficient']
    material_out = [m for m in materials if m.stock_status == 'out_of_stock']

    # Products
    product_count = Product.objects.filter(is_active=True).count()
    product_inventory = ProductInventory.objects.select_related('product').all()

    # Sales & Purchases this month
    monthly_sales = Invoice.objects.filter(
        type='sale', status='paid', issue_date__gte=month_start
    ).aggregate(total=Sum('total'))['total'] or 0

    monthly_purchases = PurchaseRecord.objects.filter(
        purchase_date__gte=month_start
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Total stats
    total_sales = Invoice.objects.filter(type='sale', status='paid').aggregate(
        total=Sum('total'))['total'] or 0
    total_purchases = PurchaseRecord.objects.aggregate(
        total=Sum('total_price'))['total'] or 0

    # Invoice stats
    invoice_count = Invoice.objects.count()
    pending_invoices = Invoice.objects.exclude(status='paid').exclude(status='cancelled').count()
    pending_amount = Invoice.objects.exclude(status='paid').exclude(status='cancelled').aggregate(
        total=Sum('remaining_amount'))['total'] or 0

    # Production
    pending_orders = ProductionOrder.objects.filter(status='pending').count()
    in_progress_orders = ProductionOrder.objects.filter(status='in_progress').count()
    completed_orders = ProductionOrder.objects.filter(status='completed').count()
    today_production = DailyProduction.objects.filter(production_date=today).count()

    # Workers
    worker_count = Worker.objects.filter(is_active=True).count()

    # Recent data
    recent_orders = ProductionOrder.objects.select_related('product').order_by('-created_at')[:8]
    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:8]

    # Chart data - last 6 months
    chart_months = []
    chart_sales = []
    chart_purchases = []
    month_names = ['ژانویه','فوریه','مارس','آوریل','مه','ژوئن','ژوئیه','اوت','سپتامبر','اکتبر','نوامبر','دسامبر']
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        chart_months.append(month_names[m - 1])
        s = Invoice.objects.filter(
            type='sale', status='paid',
            issue_date__month=m, issue_date__year=y
        ).aggregate(total=Sum('total'))['total'] or 0
        chart_sales.append(int(s))
        p = PurchaseRecord.objects.filter(
            purchase_date__month=m, purchase_date__year=y
        ).aggregate(total=Sum('total_price'))['total'] or 0
        chart_purchases.append(int(p))

    return render(request, 'dashboard/dashboard.html', {
        # Materials
        'material_low': material_low,
        'material_out': material_out,
        'total_materials': materials.count(),
        # Products
        'product_count': product_count,
        'product_inventory': product_inventory,
        # Financial
        'monthly_sales': monthly_sales,
        'monthly_purchases': monthly_purchases,
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        # Invoices
        'invoice_count': invoice_count,
        'pending_invoices': pending_invoices,
        'pending_amount': pending_amount,
        # Production
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'today_production': today_production,
        # Workers
        'worker_count': worker_count,
        # Recent
        'recent_orders': recent_orders,
        'recent_invoices': recent_invoices,
        # Charts
        'chart_months': chart_months,
        'chart_sales': chart_sales,
        'chart_purchases': chart_purchases,
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Q
from datetime import datetime, timedelta
import csv


def _parse_date(date_str):
    """Parse date string - accepts both Jalali (1403/04/15) and Gregorian (2024-07-05)."""
    if not date_str:
        return None
    from datetime import date
    try:
        date_str = date_str.strip().replace('-', '/')
        parts = date_str.split('/')
        if len(parts) != 3:
            return None
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        if y >= 1500:
            return date(y, m, d)
        # Jalali to Gregorian
        jy2 = y + 1595
        days = -355668 + (365 * jy2) + (int(jy2 / 33) * 8) + int(((jy2 % 33) + 3) / 4) + d
        if m < 7:
            days += (m - 1) * 31
        else:
            days += ((m - 7) * 30) + 186
        gy = 400 * int(days / 146097)
        days = days % 146097
        if days > 36524:
            days -= 1
            gy += 100 * int(days / 36524)
            days = days % 36524
            if days >= 365:
                days += 1
        gy += 4 * int(days / 1461)
        days = days % 1461
        if days > 365:
            gy += int((days - 1) / 365)
            days = (days - 1) % 365
        gd = days + 1
        if gd > 216: gm = 7
        elif gd > 186: gm = 6
        elif gd > 155: gm = 5
        elif gd > 124: gm = 4
        elif gd > 93: gm = 3
        elif gd > 62: gm = 2
        else: gm = 1
        if gm > 6:
            gd -= 186
        else:
            gd -= (gm - 1) * 31
        return date(gy, gm, gd)
    except Exception:
        return None


@login_required
def report_dashboard(request):
    from django.db.models import Sum, Count, Q
    from datetime import date, timedelta
    from apps.invoices.models import Invoice
    from apps.inventory.models import PurchaseRecord, ProductInventory
    from apps.products.models import Product
    from apps.materials.models import Material
    from apps.production.models import ProductionOrder

    today = date.today()
    twelve_months_ago = today - timedelta(days=365)

    # Total sales (paid invoices)
    total_sales = Invoice.objects.filter(
        type='sale', status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0

    # Total purchases
    total_purchases = PurchaseRecord.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Net profit
    net_profit = total_sales - total_purchases

    # Inventory value (materials)
    inventory_value = 0
    for m in Material.objects.filter(is_active=True):
        inventory_value += m.purchase_price * m.current_stock

    # Invoice stats
    invoice_count = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='paid').count()
    pending_amount = Invoice.objects.exclude(status='paid').aggregate(
        total=Sum('remaining_amount')
    )['total'] or 0

    product_count = Product.objects.filter(is_active=True).count()

    # Chart data - last 12 months sales/purchases
    chart_months = []
    chart_sales = []
    chart_purchases = []
    month_names = ['ژانویه','فوریه','مارس','آوریل','مه','ژوئن','ژوئیه','اوت','سپتامبر','اکتبر','نوامبر','دسامبر']
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        chart_months.append(month_names[m-1])
        s = Invoice.objects.filter(
            type='sale', status='paid',
            issue_date__month=m, issue_date__year=y
        ).aggregate(total=Sum('total'))['total'] or 0
        chart_sales.append(int(s))
        p = PurchaseRecord.objects.filter(
            purchase_date__month=m, purchase_date__year=y
        ).aggregate(total=Sum('total_price'))['total'] or 0
        chart_purchases.append(int(p))

    # Invoice status distribution
    paid = Invoice.objects.filter(status='paid').count()
    partial = Invoice.objects.filter(status='partial').count()
    draft = Invoice.objects.filter(status='draft').count()
    cancelled = Invoice.objects.filter(status='cancelled').count()
    chart_invoice_stats = [paid, partial, draft, cancelled]

    # Recent invoices
    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]

    return render(request, 'reports/report_dashboard.html', {
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'net_profit': net_profit,
        'inventory_value': inventory_value,
        'invoice_count': invoice_count,
        'paid_invoices': paid_invoices,
        'pending_amount': pending_amount,
        'product_count': product_count,
        'chart_months': chart_months,
        'chart_sales': chart_sales,
        'chart_purchases': chart_purchases,
        'chart_invoice_stats': chart_invoice_stats,
        'recent_invoices': recent_invoices,
    })


@login_required
def material_usage_report(request):
    from apps.inventory.models import InventoryTransaction
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    transactions = InventoryTransaction.objects.filter(type='out').select_related('material')
    df = _parse_date(date_from)
    dt = _parse_date(date_to)
    if df:
        transactions = transactions.filter(transaction_date__date__gte=df)
    if dt:
        transactions = transactions.filter(transaction_date__date__lte=dt)
    return render(request, 'reports/material_usage_report.html', {
        'transactions': transactions,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def production_cost_report(request):
    from apps.production.models import ProductionOrder
    orders = ProductionOrder.objects.filter(status='completed').select_related('product')
    return render(request, 'reports/production_cost_report.html', {'orders': orders})


@login_required
def profit_report(request):
    from apps.products.models import Product
    products = Product.objects.filter(is_active=True)
    product_data = []
    total_profit = 0
    margins = []
    for p in products:
        profit = p.sale_price - p.cost_price
        total_profit += profit
        margin = round(float(profit) / float(p.cost_price) * 100, 1) if p.cost_price > 0 else 0
        margins.append(margin)
        product_data.append({
            'product': p,
            'profit': profit,
            'margin': margin,
        })
    avg_margin = round(sum(margins) / len(margins), 1) if margins else 0
    return render(request, 'reports/profit_report.html', {
        'product_data': product_data,
        'total_profit': total_profit,
        'avg_margin': avg_margin,
    })


@login_required
def purchase_report(request):
    from apps.inventory.models import PurchaseRecord
    purchases = PurchaseRecord.objects.select_related('material').all()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    df = _parse_date(date_from)
    dt = _parse_date(date_to)
    if df:
        purchases = purchases.filter(purchase_date__gte=df)
    if dt:
        purchases = purchases.filter(purchase_date__lte=dt)
    return render(request, 'reports/purchase_report.html', {
        'purchases': purchases,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def inventory_report(request):
    from apps.materials.models import Material
    from apps.inventory.models import ProductInventory
    materials = Material.objects.filter(is_active=True)
    products = ProductInventory.objects.select_related('product').all()
    total_materials = materials.count()
    sufficient_count = sum(1 for m in materials if m.stock_status == 'sufficient')
    low_count = sum(1 for m in materials if m.stock_status == 'low')
    out_count = sum(1 for m in materials if m.stock_status == 'out_of_stock')
    return render(request, 'reports/inventory_report.html', {
        'materials': materials,
        'products': products,
        'total_materials': total_materials,
        'sufficient_count': sufficient_count,
        'low_count': low_count,
        'out_count': out_count,
    })


@login_required
def product_price_list(request):
    from apps.products.models import Product
    products = Product.objects.filter(is_active=True)
    return render(request, 'reports/product_price_list.html', {'products': products})


@login_required
def price_change_report(request):
    from apps.materials.models import MaterialPriceHistory
    history = MaterialPriceHistory.objects.select_related('material', 'changed_by').all()
    return render(request, 'reports/price_change_report.html', {'history': history})


@login_required
def financial_summary(request):
    from apps.invoices.models import Invoice
    from apps.inventory.models import PurchaseRecord
    from apps.production.models import ProductionOrder
    month = request.GET.get('month', datetime.now().month)
    year = request.GET.get('year', datetime.now().year)
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = datetime.now().month
        year = datetime.now().year
    sales = Invoice.objects.filter(type='sale', status='paid', issue_date__month=month, issue_date__year=year)
    total_sales = sales.aggregate(total=Sum('total'))['total'] or 0
    purchases = PurchaseRecord.objects.filter(purchase_date__month=month, purchase_date__year=year)
    total_purchases = purchases.aggregate(total=Sum('total_price'))['total'] or 0
    production_costs = ProductionOrder.objects.filter(status='completed', end_date__month=month, end_date__year=year)
    total_production = production_costs.aggregate(total=Sum('total_cost'))['total'] or 0
    combined_costs = total_purchases + total_production
    profit = total_sales - combined_costs
    profit_margin = round(float(profit) / float(total_sales) * 100, 1) if total_sales > 0 else 0
    return render(request, 'reports/financial_summary.html', {
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'total_production': total_production,
        'combined_costs': combined_costs,
        'profit': profit,
        'profit_margin': profit_margin,
        'month': month,
        'year': year,
    })


@login_required
def export_csv(request, report_type):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{report_type}.csv"'
    writer = csv.writer(response)
    if report_type == 'materials':
        from apps.materials.models import Material
        writer.writerow(['کد', 'نام', 'دسته‌بندی', 'واحد', 'قیمت خرید', 'موجودی'])
        for m in Material.objects.all():
            writer.writerow([m.code, m.name, m.category.name, m.get_unit_display(), m.purchase_price, m.current_stock])
    elif report_type == 'products':
        from apps.products.models import Product
        writer.writerow(['کد', 'نام', 'قیمت تمام‌شده', 'قیمت فروش'])
        for p in Product.objects.all():
            writer.writerow([p.code, p.name, p.cost_price, p.sale_price])
    return response


@login_required
def invoice_report(request):
    from apps.invoices.models import Invoice
    invoices = Invoice.objects.select_related('customer').all()
    status = request.GET.get('status', '')
    if status:
        invoices = invoices.filter(status=status)
    total_amount = invoices.aggregate(total=Sum('total'))['total'] or 0
    total_paid = invoices.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_remaining = invoices.aggregate(total=Sum('remaining_amount'))['total'] or 0
    return render(request, 'reports/invoice_report.html', {
        'invoices': invoices,
        'status': status,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
    })


@login_required
def worker_report(request):
    from apps.workers.models import Worker
    from apps.production.models import DailyProduction
    workers = Worker.objects.filter(is_active=True)
    worker_data = []
    for w in workers:
        prods = DailyProduction.objects.filter(worker=w).values('product__name').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')
        count = DailyProduction.objects.filter(worker=w).count()
        first = DailyProduction.objects.filter(worker=w).order_by('production_date').first()
        last = DailyProduction.objects.filter(worker=w).order_by('-production_date').first()
        total_qty = sum(p['total_qty'] for p in prods)
        worker_data.append({
            'worker': w,
            'total_qty': total_qty,
            'count': count,
            'first_date': first.production_date if first else None,
            'last_date': last.production_date if last else None,
            'products_list': list(prods[:5]),
        })
    return render(request, 'reports/worker_report.html', {'worker_data': worker_data})

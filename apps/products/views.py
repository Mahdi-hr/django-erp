from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, ProductMaterial
from .forms import ProductForm, ProductMaterialFormSet
from .services import calculate_product_cost


def _get_cost_context():
    """Get material prices and fixed cost totals for the template."""
    import json
    from decimal import Decimal
    from apps.materials.models import Material
    from apps.common.models import Setting
    from apps.settings_app.models import FixedCost

    # All material prices keyed by id
    prices = {}
    for m in Material.objects.all():
        prices[m.pk] = float(m.purchase_price)

    # Sum of fixed costs + service costs
    monthly_fixed = Decimal('0')
    for fc in FixedCost.objects.filter(is_active=True):
        monthly_fixed += fc.amount

    water_cost = Decimal(Setting.get_value('water_cost', '0'))
    electricity_cost = Decimal(Setting.get_value('electricity_cost', '0'))
    gas_cost = Decimal(Setting.get_value('gas_cost', '0'))

    fixed_total = int(monthly_fixed + water_cost + electricity_cost + gas_cost)

    return {
        'material_prices_json': json.dumps(prices),
        'fixed_cost_total': fixed_total,
    }


@login_required
def product_list(request):
    products = Product.objects.all()
    search = request.GET.get('search', '')
    if search:
        from django.db.models import Q
        products = products.filter(Q(name__icontains=search) | Q(code__icontains=search))
    return render(request, 'products/product_list.html', {'products': products, 'search': search})


@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductMaterialFormSet(request.POST)
        if form.is_valid():
            product = form.save()
            formset = ProductMaterialFormSet(request.POST, instance=product)
            if formset.is_valid():
                formset.save()
                calculate_product_cost(product)
                # Save initial stock
                from apps.inventory.models import ProductInventory
                stock = form.cleaned_data.get('current_stock') or 0
                pi, _ = ProductInventory.objects.get_or_create(product=product)
                pi.current_stock = stock
                pi.save(update_fields=['current_stock'])
                messages.success(request, 'محصول با موفقیت ایجاد شد')
                return redirect('product_list')
    else:
        form = ProductForm()
        formset = ProductMaterialFormSet()
    ctx = {'form': form, 'formset': formset, 'title': 'ایجاد محصول جدید'}
    ctx.update(_get_cost_context())
    return render(request, 'products/product_form.html', ctx)


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = ProductMaterialFormSet(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            if formset.is_valid():
                formset.save()
                calculate_product_cost(product)
                # Save stock
                from apps.inventory.models import ProductInventory
                stock = form.cleaned_data.get('current_stock') or 0
                pi, _ = ProductInventory.objects.get_or_create(product=product)
                pi.current_stock = stock
                pi.save(update_fields=['current_stock'])
                messages.success(request, 'محصول با موفقیت ویرایش شد')
                return redirect('product_list')
    else:
        form = ProductForm(instance=product)
        formset = ProductMaterialFormSet(instance=product)
    ctx = {'form': form, 'formset': formset, 'title': 'ویرایش محصول', 'product': product}
    # Add current stock to form initial
    from apps.inventory.models import ProductInventory
    try:
        pi = ProductInventory.objects.get(product=product)
        ctx['current_stock'] = pi.current_stock
        form.fields['current_stock'].initial = pi.current_stock
    except ProductInventory.DoesNotExist:
        ctx['current_stock'] = 0
        form.fields['current_stock'].initial = 0
    ctx.update(_get_cost_context())
    return render(request, 'products/product_form.html', ctx)


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'محصول با موفقیت حذف شد')
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'object': product})


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    materials = product.materials.select_related('material').all()
    return render(request, 'products/product_detail.html', {
        'product': product,
        'materials': materials,
    })


@login_required
def recalculate_all_costs(request):
    from apps.products.services import recalculate_all_products
    recalculate_all_products()
    messages.success(request, 'قیمت تمام‌شده تمام محصولات بازمحاسبه شد')
    return redirect('product_list')


@login_required
def api_material_prices(request):
    """AJAX endpoint: return current material prices and fixed costs."""
    import json
    from decimal import Decimal
    from apps.materials.models import Material
    from apps.common.models import Setting
    from apps.settings_app.models import FixedCost

    prices = {}
    for m in Material.objects.all():
        prices[str(m.pk)] = float(m.purchase_price)

    monthly_fixed = Decimal('0')
    for fc in FixedCost.objects.filter(is_active=True):
        monthly_fixed += fc.amount

    water_cost = Decimal(Setting.get_value('water_cost', '0'))
    electricity_cost = Decimal(Setting.get_value('electricity_cost', '0'))
    gas_cost = Decimal(Setting.get_value('gas_cost', '0'))
    fixed_total = int(monthly_fixed + water_cost + electricity_cost + gas_cost)

    return JsonResponse({'prices': prices, 'fixed_cost': fixed_total})


@login_required
def product_export_employer_excel(request):
    """Export products Excel for employer (all prices)."""
    from apps.common.export_utils import generate_products_excel
    return generate_products_excel(mode='employer')


@login_required
def product_export_customer_excel(request):
    """Export products Excel for customer (sale prices only)."""
    from apps.common.export_utils import generate_products_excel
    return generate_products_excel(mode='customer')


@login_required
def product_print_employer(request):
    """Print products page for employer (all prices)."""
    from apps.products.models import Product
    from apps.common.export_utils import _get_company_info
    import jdatetime

    products = Product.objects.filter(is_active=True)
    now = jdatetime.datetime.now()

    header_html = '<th style="width:28px;">#</th><th style="width:55px;">کد</th><th>نام محصول</th><th>قیمت تمام‌شده</th><th>قیمت فروش</th><th style="width:42px;">سود</th><th>عمده</th><th>جزئی</th><th>نمایندگی</th><th>صادراتی</th><th>ویژه</th>'

    rows = []
    for i, p in enumerate(products, 1):
        rows.append(f'''<tr>
            <td class="row-num">{i}</td>
            <td class="col-code">{p.code}</td>
            <td class="col-name">{p.name}</td>
            <td class="col-cost">{p.cost_price:,.0f}</td>
            <td class="col-price">{p.sale_price:,.0f}</td>
            <td class="col-profit">{p.profit_percent}%</td>
            <td class="col-mult">{p.wholesale_price:,.0f}</td>
            <td class="col-mult">{p.retail_price:,.0f}</td>
            <td class="col-mult">{p.dealer_price:,.0f}</td>
            <td class="col-mult">{p.export_price:,.0f}</td>
            <td class="col-mult">{p.special_price:,.0f}</td>
        </tr>''')

    return render(request, 'common/print_report.html', {
        'title': 'لیست محصولات',
        'subtitle': 'گزارش جامع — تمام قیمت‌ها',
        'icon': 'box',
        'company': _get_company_info(),
        'back_url': '/products/',
        'total_count': products.count(),
        'count_label': 'تعداد محصولات',
        'jalali_date': now.strftime('%Y/%m/%d'),
        'jalali_time': now.strftime('%H:%M'),
        'header_html': header_html,
        'body_html': '\n'.join(rows),
    })


@login_required
def product_print_customer(request):
    """Print products page for customer (sale prices only)."""
    from apps.products.models import Product
    from apps.common.export_utils import _get_company_info
    import jdatetime

    products = Product.objects.filter(is_active=True)
    now = jdatetime.datetime.now()

    header_html = '<th style="width:35px;">#</th><th style="width:60px;">کد</th><th>نام محصول</th><th style="width:130px;">قیمت فروش (ریال)</th>'

    rows = []
    for i, p in enumerate(products, 1):
        rows.append(f'''<tr>
            <td class="row-num">{i}</td>
            <td class="col-code">{p.code}</td>
            <td class="col-name">{p.name}</td>
            <td class="col-price">{p.sale_price:,.0f}</td>
        </tr>''')

    return render(request, 'common/print_report.html', {
        'title': 'لیست قیمت محصولات',
        'subtitle': 'فقط قیمت‌های فروش',
        'icon': 'tags',
        'company': _get_company_info(),
        'back_url': '/products/',
        'total_count': products.count(),
        'count_label': 'تعداد محصولات',
        'jalali_date': now.strftime('%Y/%m/%d'),
        'jalali_time': now.strftime('%H:%M'),
        'header_html': header_html,
        'body_html': '\n'.join(rows),
    })

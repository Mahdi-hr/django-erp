from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import MaterialCategory, Material, MaterialPriceHistory
from .forms import MaterialCategoryForm, MaterialForm


@login_required
def category_list(request):
    categories = MaterialCategory.objects.all()
    return render(request, 'materials/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    if request.method == 'POST':
        form = MaterialCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'دسته‌بندی با موفقیت ایجاد شد')
            return redirect('category_list')
    else:
        form = MaterialCategoryForm()
    return render(request, 'materials/category_form.html', {'form': form, 'title': 'ایجاد دسته‌بندی'})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(MaterialCategory, pk=pk)
    if request.method == 'POST':
        form = MaterialCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'دسته‌بندی با موفقیت ویرایش شد')
            return redirect('category_list')
    else:
        form = MaterialCategoryForm(instance=category)
    return render(request, 'materials/category_form.html', {'form': form, 'title': 'ویرایش دسته‌بندی'})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(MaterialCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'دسته‌بندی با موفقیت حذف شد')
        return redirect('category_list')
    return render(request, 'materials/category_confirm_delete.html', {'object': category})


@login_required
def material_list(request):
    materials = Material.objects.select_related('category').all()
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    if search:
        materials = materials.filter(Q(name__icontains=search) | Q(code__icontains=search))
    if category:
        materials = materials.filter(category_id=category)
    categories = MaterialCategory.objects.filter(is_active=True)
    return render(request, 'materials/material_list.html', {
        'materials': materials,
        'categories': categories,
        'search': search,
        'selected_category': category,
    })


@login_required
def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'ماده اولیه با موفقیت ایجاد شد')
            return redirect('material_list')
    else:
        form = MaterialForm()
    return render(request, 'materials/material_form.html', {'form': form, 'title': 'ایجاد ماده اولیه'})


@login_required
def material_edit(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'ماده اولیه با موفقیت ویرایش شد')
            return redirect('material_list')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'materials/material_form.html', {'form': form, 'title': 'ویرایش ماده اولیه'})


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'ماده اولیه با موفقیت حذف شد')
        return redirect('material_list')
    return render(request, 'materials/material_confirm_delete.html', {'object': material})


@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material, pk=pk)
    price_history = MaterialPriceHistory.objects.filter(material=material)[:20]
    return render(request, 'materials/material_detail.html', {
        'material': material,
        'price_history': price_history,
    })


@login_required
def material_export_excel(request):
    """Export materials Excel with all details."""
    from apps.common.export_utils import generate_materials_excel
    return generate_materials_excel()


@login_required
def material_print(request):
    """Print materials page (unified design)."""
    from apps.materials.models import Material
    from apps.common.export_utils import _get_company_info
    import jdatetime

    materials = Material.objects.filter(is_active=True).select_related('category')
    now = jdatetime.datetime.now()
    out_count = sum(1 for m in materials if m.stock_status == 'out_of_stock')
    low_count = sum(1 for m in materials if m.stock_status == 'low')

    header_html = '<th style="width:28px;">#</th><th style="width:55px;">کد</th><th>نام ماده</th><th style="width:70px;">دسته‌بندی</th><th style="width:42px;">واحد</th><th style="width:75px;">قیمت خرید</th><th style="width:50px;">موجودی</th><th style="width:50px;">حداقل</th><th style="width:60px;">وضعیت</th>'

    status_map = {'sufficient': ('کافی', 'status-ok', 'check-circle'), 'low': ('کمبود', 'status-low', 'exclamation-triangle'), 'out_of_stock': ('ناموجود', 'status-out', 'times-circle')}

    rows = []
    for i, m in enumerate(materials, 1):
        label, cls, icon = status_map.get(m.stock_status, ('کافی', 'status-ok', 'check-circle'))
        stock_color = '#dc2626' if m.stock_status == 'out_of_stock' else '#d97706' if m.stock_status == 'low' else '#16a34a'
        rows.append(f'''<tr>
            <td class="row-num">{i}</td>
            <td class="col-code">{m.code}</td>
            <td class="col-name">{m.name}</td>
            <td>{m.category.name}</td>
            <td>{m.get_unit_display_fa()}</td>
            <td class="col-price">{m.purchase_price:,.0f}</td>
            <td class="col-stock" style="color:{stock_color};">{m.current_stock}</td>
            <td>{m.min_stock}</td>
            <td><span class="status-pill {cls}"><i class="fas fa-{icon}" style="font-size:0.55rem;"></i> {label}</span></td>
        </tr>''')

    return render(request, 'common/print_report.html', {
        'title': 'مواد اولیه',
        'subtitle': 'گزارش جامع — موجودی و قیمت',
        'icon': 'cubes',
        'company': _get_company_info(),
        'back_url': '/materials/',
        'total_count': materials.count(),
        'count_label': 'تعداد مواد',
        'jalali_date': now.strftime('%Y/%m/%d'),
        'jalali_time': now.strftime('%H:%M'),
        'header_html': header_html,
        'body_html': '\n'.join(rows),
    })

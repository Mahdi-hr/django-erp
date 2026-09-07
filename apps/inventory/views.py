from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import InventoryTransaction, PurchaseRecord, WasteRecord, ReturnRecord, ProductInventory, ProductInventoryTransaction, ProductPurchase
from .forms import PurchaseRecordForm, PurchaseRecordFormSet, WasteRecordForm, ReturnRecordForm, ProductPurchaseForm, ProductPurchaseFormSet
from apps.common.decorators import role_required


@login_required
def inventory_dashboard(request):
    from apps.materials.models import Material

    # Materials section - paginated
    materials_qs = Material.objects.filter(is_active=True).select_related('category')
    material_low_stock = [m for m in materials_qs if m.stock_status != 'sufficient']
    materials_paginator = Paginator(materials_qs, 10)
    materials_page = request.GET.get('materials_page')
    materials = materials_paginator.get_page(materials_page)

    # Products section - paginated
    product_inventories_qs = ProductInventory.objects.select_related('product').all()
    products_paginator = Paginator(product_inventories_qs, 10)
    products_page = request.GET.get('products_page')
    product_inventories = products_paginator.get_page(products_page)

    # Recent transactions - paginated
    transactions_qs = InventoryTransaction.objects.select_related('material').all()
    transactions_paginator = Paginator(transactions_qs, 10)
    transactions_page = request.GET.get('transactions_page')
    transactions = transactions_paginator.get_page(transactions_page)

    # Product transactions - paginated
    product_transactions_qs = ProductInventoryTransaction.objects.select_related('product').all()
    product_tx_paginator = Paginator(product_transactions_qs, 10)
    product_tx_page = request.GET.get('product_tx_page')
    product_transactions = product_tx_paginator.get_page(product_tx_page)

    return render(request, 'inventory/inventory_dashboard.html', {
        'materials': materials,
        'material_low_stock': material_low_stock,
        'product_inventories': product_inventories,
        'transactions': transactions,
        'product_transactions': product_transactions,
    })


@login_required
def purchase_list(request):
    purchases = PurchaseRecord.objects.select_related('material').all()
    return render(request, 'inventory/purchase_list.html', {'purchases': purchases})


@login_required
@role_required('admin', 'warehouse')
def purchase_create(request):
    import json
    from apps.materials.models import Material
    prices = {str(m.pk): float(m.purchase_price) for m in Material.objects.all()}

    if request.method == 'POST':
        formset = PurchaseRecordFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    purchase = form.save(commit=False)
                    purchase.total_price = purchase.quantity * purchase.unit_price
                    purchase.created_by = request.user
                    purchase.save()
            # Check for low stock materials
            from apps.common.models import notify_admins
            low_stock = Material.objects.filter(current_stock__lte=models.F('min_stock'), is_active=True)
            for mat in low_stock[:5]:
                notify_admins(
                    'موجودی کم',
                    f'موجودی {mat.name} به {mat.current_stock} {mat.get_unit_display()} رسیده (حداقل: {mat.min_stock})',
                    'warning',
                    'material',
                    mat.pk,
                )
            messages.success(request, 'خرید با موفقیت ثبت شد')
            return redirect('purchase_list')
    else:
        formset = PurchaseRecordFormSet()
    return render(request, 'inventory/purchase_form.html', {
        'formset': formset, 'title': 'ثبت خرید جدید',
        'material_prices_json': json.dumps(prices),
    })


@login_required
def waste_list(request):
    wastes = WasteRecord.objects.select_related('material').all()
    return render(request, 'inventory/waste_list.html', {'wastes': wastes})


@login_required
@role_required('admin', 'warehouse')
def waste_create(request):
    if request.method == 'POST':
        form = WasteRecordForm(request.POST)
        if form.is_valid():
            waste = form.save(commit=False)
            waste.created_by = request.user
            # Validate stock availability
            material = waste.material
            if waste.quantity > material.current_stock:
                messages.error(request, f'موجودی {material.name} کافی نیست! موجودی فعلی: {material.current_stock} {material.get_unit_display()}')
                return render(request, 'inventory/waste_form.html', {'form': form, 'title': 'ثبت ضایعات'})
            waste.save()
            messages.success(request, 'ضایعات با موفقیت ثبت شد')
            return redirect('waste_list')
    else:
        form = WasteRecordForm()
    return render(request, 'inventory/waste_form.html', {'form': form, 'title': 'ثبت ضایعات'})


@login_required
@role_required('admin', 'warehouse')
def waste_delete(request, pk):
    waste = get_object_or_404(WasteRecord, pk=pk)
    if request.method == 'POST':
        waste.material.current_stock += waste.quantity
        waste.material.save(update_fields=['current_stock'])
        InventoryTransaction.objects.filter(
            reference_type='waste', reference_id=waste.pk, material=waste.material
        ).delete()
        waste.delete()
        messages.success(request, 'ضایعات حذف شد و موجودی بازگردانده شد')
        return redirect('waste_list')
    return render(request, 'inventory/purchase_confirm_delete.html', {'object': waste})


@login_required
def return_list(request):
    returns = ReturnRecord.objects.select_related('material').all()
    return render(request, 'inventory/return_list.html', {'returns': returns})


@login_required
@role_required('admin', 'warehouse')
def return_create(request):
    if request.method == 'POST':
        form = ReturnRecordForm(request.POST)
        if form.is_valid():
            ret = form.save(commit=False)
            ret.created_by = request.user
            ret.save()
            messages.success(request, 'برگشت با موفقیت ثبت شد')
            return redirect('return_list')
    else:
        form = ReturnRecordForm()
    return render(request, 'inventory/return_form.html', {'form': form, 'title': 'ثبت برگشت'})


@login_required
@role_required('admin', 'warehouse')
def return_delete(request, pk):
    ret = get_object_or_404(ReturnRecord, pk=pk)
    if request.method == 'POST':
        ret.material.current_stock -= ret.quantity
        if ret.material.current_stock < 0:
            ret.material.current_stock = 0
        ret.material.save(update_fields=['current_stock'])
        InventoryTransaction.objects.filter(
            reference_type='return', reference_id=ret.pk, material=ret.material
        ).delete()
        ret.delete()
        messages.success(request, 'برگشت حذف شد و موجودی بازگردانده شد')
        return redirect('return_list')
    return render(request, 'inventory/purchase_confirm_delete.html', {'object': ret})


@login_required
@role_required('admin', 'warehouse')
def purchase_delete(request, pk):
    purchase = get_object_or_404(PurchaseRecord, pk=pk)
    if request.method == 'POST':
        purchase.material.current_stock -= purchase.quantity
        if purchase.material.current_stock < 0:
            purchase.material.current_stock = 0
        purchase.material.save(update_fields=['current_stock'])
        InventoryTransaction.objects.filter(
            reference_type='purchase', reference_id=purchase.pk, material=purchase.material
        ).delete()
        purchase.delete()
        messages.success(request, 'خرید حذف شد و موجودی بازگردانده شد')
        return redirect('purchase_list')
    return render(request, 'inventory/purchase_confirm_delete.html', {'object': purchase})


@login_required
@role_required('admin', 'warehouse')
def product_purchase_delete(request, pk):
    purchase = get_object_or_404(ProductPurchase, pk=pk)
    if request.method == 'POST':
        pi, _ = ProductInventory.objects.get_or_create(product=purchase.product)
        pi.current_stock -= purchase.quantity
        if pi.current_stock < 0:
            pi.current_stock = 0
        pi.save(update_fields=['current_stock'])
        ProductInventoryTransaction.objects.filter(
            reference_type='product_purchase', reference_id=purchase.pk, product=purchase.product
        ).delete()
        purchase.delete()
        messages.success(request, 'خرید حذف شد و موجودی بازگردانده شد')
        return redirect('product_purchase_list')
    return render(request, 'inventory/purchase_confirm_delete.html', {'object': purchase})


@login_required
def product_inventory_list(request):
    inventories = ProductInventory.objects.select_related('product').all()
    return render(request, 'inventory/product_inventory_list.html', {'inventories': inventories})


@login_required
def transaction_list(request):
    transactions = InventoryTransaction.objects.select_related('material').all()
    material = request.GET.get('material', '')
    type_filter = request.GET.get('type', '')
    if material:
        transactions = transactions.filter(material_id=material)
    if type_filter:
        transactions = transactions.filter(type=type_filter)
    from apps.materials.models import Material
    materials = Material.objects.filter(is_active=True)
    return render(request, 'inventory/transaction_list.html', {
        'transactions': transactions,
        'materials': materials,
        'selected_material': material,
        'selected_type': type_filter,
    })


@login_required
def product_purchase_list(request):
    purchases = ProductPurchase.objects.select_related('product').all()
    return render(request, 'inventory/product_purchase_list.html', {'purchases': purchases})


@login_required
@role_required('admin', 'warehouse')
def product_purchase_create(request):
    import json
    from apps.products.models import Product
    prices = {str(p.pk): float(p.cost_price) for p in Product.objects.filter(is_active=True)}

    if request.method == 'POST':
        formset = ProductPurchaseFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    product = form.cleaned_data.get('product')
                    if product:
                        purchase = form.save(commit=False)
                        purchase.total_price = purchase.quantity * purchase.unit_price
                        purchase.created_by = request.user
                        purchase.save()
            messages.success(request, 'خرید محصول با موفقیت ثبت شد')
            return redirect('product_purchase_list')
    else:
        formset = ProductPurchaseFormSet()
    return render(request, 'inventory/product_purchase_form.html', {
        'formset': formset, 'title': 'ثبت خرید محصول',
        'product_prices_json': json.dumps(prices),
    })


@login_required
def product_inventory_detail(request, pk):
    inv = get_object_or_404(ProductInventory, pk=pk)
    transactions = ProductInventoryTransaction.objects.filter(product=inv.product).select_related('product')[:30]
    return render(request, 'inventory/product_inventory_detail.html', {
        'inventory': inv,
        'transactions': transactions,
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import ProductionOrder, ProductionMaterial, DailyProduction
from apps.products.models import Product
from apps.workers.models import Worker


@login_required
def order_list(request):
    orders = ProductionOrder.objects.select_related('product').all()
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'production/order_list.html', {'orders': orders, 'status': status})


@login_required
def order_create(request):
    if request.method == 'POST':
        form = ProductionOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.unit_cost = order.product.cost_price
            order.total_cost = order.unit_cost * order.quantity
            order.save()
            for pm in order.product.materials.all():
                ProductionMaterial.objects.create(
                    order=order,
                    material=pm.material,
                    planned_quantity=pm.quantity * order.quantity,
                    unit_cost=pm.material.purchase_price,
                    total_cost=pm.material.purchase_price * pm.quantity * order.quantity,
                )
            messages.success(request, 'سفارش تولید با موفقیت ایجاد شد')
            return redirect('order_list')
    else:
        form = ProductionOrderForm()
    return render(request, 'production/order_form.html', {'form': form, 'title': 'ایجاد سفارش تولید'})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    materials = order.materials.select_related('material').all()
    return render(request, 'production/order_detail.html', {'order': order, 'materials': materials})


@login_required
def order_start(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    if order.status != 'pending':
        messages.error(request, 'فقط سفارشات در انتظار قابل شروع هستند')
        return redirect('order_detail', pk=pk)
    order.status = 'in_progress'
    order.start_date = timezone.now().date()
    order.save(update_fields=['status', 'start_date'])
    messages.success(request, 'تولید شروع شد')
    return redirect('order_detail', pk=pk)


@login_required
def order_complete(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    if order.status != 'in_progress':
        messages.error(request, 'فقط سفارشات در حال تولید قابل تکمیل هستند')
        return redirect('order_detail', pk=pk)
    try:
        order.complete_production()
        messages.success(request, 'تولید با موفقیت تکمیل شد')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('order_detail', pk=pk)


@login_required
def order_cancel(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    if order.status not in ('pending', 'in_progress'):
        messages.error(request, 'این سفارش قابل لغو نیست')
        return redirect('order_detail', pk=pk)
    order.status = 'cancelled'
    order.save(update_fields=['status'])
    messages.success(request, 'سفارش لغو شد')
    return redirect('order_list')


@login_required
def daily_production_list(request):
    productions = DailyProduction.objects.select_related('worker', 'product').all()
    return render(request, 'production/daily_production_list.html', {'productions': productions})


@login_required
def daily_production_create(request):
    products = Product.objects.all()
    workers = Worker.objects.all()

    if request.method == 'POST':
        worker_id = request.POST.get('worker')
        production_date = request.POST.get('production_date')
        notes = request.POST.get('notes', '')

        if not worker_id or not production_date:
            messages.error(request, 'کارگر و تاریخ الزامی هستند')
            return render(request, 'production/daily_production_form.html', {
                'workers': workers, 'products': products,
                'title': 'ثبت تولید روزانه',
            })

        worker = Worker.objects.get(pk=worker_id)
        created_count = 0
        errors = []

        # Collect all product rows
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')

        for i, (pid, qty) in enumerate(zip(product_ids, quantities)):
            if not pid or not qty:
                continue
            try:
                product = Product.objects.get(pk=pid)
                quantity = int(qty)
                if quantity <= 0:
                    errors.append(f'تعداد {product.name} باید بزرگتر از صفر باشد')
                    continue
            except (Product.DoesNotExist, ValueError):
                errors.append(f'ردیف {i+1}: اطلاعات نامعتبر')
                continue

            dp = DailyProduction(
                worker=worker,
                product=product,
                quantity=quantity,
                production_date=production_date,
                notes=notes,
                created_by=request.user,
                status='completed',
            )
            dp.save()
            try:
                dp.apply_inventory()
                created_count += 1
            except ValueError as e:
                dp.delete()
                errors.append(f'{product.name}: {str(e)}')

        if created_count > 0:
            messages.success(request, f'{created_count} ردیف تولید با موفقیت ثبت شد')
        for err in errors:
            messages.error(request, err)

        if created_count > 0:
            return redirect('daily_production_list')
        return render(request, 'production/daily_production_form.html', {
            'workers': workers, 'products': products,
            'title': 'ثبت تولید روزانه',
        })

    return render(request, 'production/daily_production_form.html', {
        'workers': workers, 'products': products,
        'title': 'ثبت تولید روزانه',
    })


@login_required
def daily_production_edit(request, pk):
    dp = get_object_or_404(DailyProduction, pk=pk)
    products = Product.objects.all()
    workers = Worker.objects.all()

    if request.method == 'POST':
        worker_id = request.POST.get('worker')
        production_date = request.POST.get('production_date')
        notes = request.POST.get('notes', '')
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')

        if worker_id and production_date:
            worker = Worker.objects.get(pk=worker_id)
            dp.reverse_inventory()
            dp.worker = worker
            dp.production_date = production_date
            dp.notes = notes
            dp.created_by = request.user

            if product_ids and quantities:
                dp.product = Product.objects.get(pk=product_ids[0])
                dp.quantity = int(quantities[0])
                dp.save()
                try:
                    dp.apply_inventory()
                    messages.success(request, 'تولید روزانه با موفقیت ویرایش شد')
                except ValueError as e:
                    messages.error(request, str(e))
                return redirect('daily_production_list')

    return render(request, 'production/daily_production_form.html', {
        'workers': workers, 'products': products,
        'dp': dp, 'title': 'ویرایش تولید روزانه',
    })


@login_required
def daily_production_delete(request, pk):
    dp = get_object_or_404(DailyProduction, pk=pk)
    if request.method == 'POST':
        dp.reverse_inventory()
        dp.delete()
        messages.success(request, 'تولید روزانه حذف شد')
        return redirect('daily_production_list')
    return render(request, 'production/daily_production_confirm_delete.html', {'object': dp})

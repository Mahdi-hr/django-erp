from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Worker
from .forms import WorkerForm


def jalali_to_gregorian(jalali_str):
    """تبدیل تاریخ شمسی (1403/04/10) به میلادی"""
    if not jalali_str:
        return None
    try:
        parts = str(jalali_str).strip().replace('-', '/').split('/')
        if len(parts) != 3:
            return None
        jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
        import jdatetime
        return jdatetime.date(jy, jm, jd).togregorian()
    except Exception:
        return None


@login_required
def worker_list(request):
    workers = Worker.objects.all()

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    if search:
        workers = workers.filter(Q(name__icontains=search) | Q(phone__icontains=search))

    date_from_g = jalali_to_gregorian(date_from)
    date_to_g = jalali_to_gregorian(date_to)

    from apps.production.models import DailyProduction
    worker_stats = {}
    for w in workers:
        dps = DailyProduction.objects.filter(worker=w, status='completed')
        if date_from_g:
            dps = dps.filter(production_date__gte=date_from_g)
        if date_to_g:
            dps = dps.filter(production_date__lte=date_to_g)

        total_qty = dps.aggregate(total=Sum('quantity'))['total'] or 0
        count = dps.count()
        first_date = dps.order_by('production_date').values_list('production_date', flat=True).first()
        last_date = dps.order_by('-production_date').values_list('production_date', flat=True).first()
        products = dps.values('product__name', 'product__code').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')
        worker_stats[w.pk] = {
            'total_qty': total_qty,
            'count': count,
            'first_date': first_date,
            'last_date': last_date,
            'products': list(products),
        }

    return render(request, 'workers/worker_list.html', {
        'workers': workers,
        'worker_stats': worker_stats,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    })


@login_required
def worker_detail(request, pk):
    worker = get_object_or_404(Worker, pk=pk)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    date_from_g = jalali_to_gregorian(date_from)
    date_to_g = jalali_to_gregorian(date_to)

    from apps.production.models import DailyProduction

    productions = DailyProduction.objects.filter(worker=worker).select_related('product').order_by('-production_date')
    if date_from_g:
        productions = productions.filter(production_date__gte=date_from_g)
    if date_to_g:
        productions = productions.filter(production_date__lte=date_to_g)

    completed = productions.filter(status='completed')
    total_qty = completed.aggregate(total=Sum('quantity'))['total'] or 0
    total_records = completed.count()

    products_summary = completed.values('product__name', 'product__code').annotate(
        total_qty=Sum('quantity'),
    ).order_by('-total_qty')

    daily_summary = completed.values('production_date').annotate(
        daily_qty=Sum('quantity')
    ).order_by('-production_date')

    return render(request, 'workers/worker_detail.html', {
        'worker': worker,
        'productions': productions,
        'total_qty': total_qty,
        'total_records': total_records,
        'products_summary': products_summary,
        'daily_summary': daily_summary,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def worker_create(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'کارگر با موفقیت ایجاد شد')
            return redirect('worker_list')
    else:
        form = WorkerForm()
    return render(request, 'workers/worker_form.html', {'form': form, 'title': 'ایجاد کارگر'})


@login_required
def worker_edit(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'کارگر با موفقیت ویرایش شد')
            return redirect('worker_list')
    else:
        form = WorkerForm(instance=worker)
    return render(request, 'workers/worker_form.html', {'form': form, 'title': 'ویرایش کارگر', 'worker': worker})


@login_required
def worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.method == 'POST':
        worker.delete()
        messages.success(request, 'کارگر با موفقیت حذف شد')
        return redirect('worker_list')
    return render(request, 'workers/worker_confirm_delete.html', {'object': worker})

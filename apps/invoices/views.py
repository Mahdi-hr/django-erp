from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet, PaymentForm
from apps.common.models import Setting


def _get_product_prices():
    import json
    from apps.products.models import Product
    prices = {}
    for p in Product.objects.filter(is_active=True):
        prices[str(p.pk)] = float(p.sale_price)
    return json.dumps(prices)


def _get_tax_rate():
    return int(Setting.get_value('tax_rate', '10'))


def _get_company_info():
    return {
        'name': Setting.get_value('company_name', 'شرکت'),
        'address': Setting.get_value('company_address', ''),
        'phone': Setting.get_value('company_phone', ''),
        'logo': Setting.get_value('company_logo', 'fa-industry'),
    }


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('customer').all()
    status = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    if status:
        invoices = invoices.filter(status=status)
    if type_filter:
        invoices = invoices.filter(type=type_filter)
    return render(request, 'invoices/invoice_list.html', {
        'invoices': invoices,
        'status': status,
        'type_filter': type_filter,
    })


@login_required
def invoice_create(request):
    tax_percent = _get_tax_rate()
    stock_errors = []
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            formset = InvoiceItemFormSet(request.POST, instance=invoice)
            if formset.is_valid():
                formset.save()
                invoice.calculate_totals()
                # Check stock if deduct_stock is checked
                if invoice.deduct_stock:
                    stock_errors = invoice.check_stock_availability()
                    if stock_errors:
                        # Delete the saved invoice and return with errors
                        invoice.delete()
                        messages.error(request, 'موجودی کافی نیست! لطفاً مقادیر را بررسی کنید.')
                        return render(request, 'invoices/invoice_form.html', {
                            'form': form, 'formset': formset, 'title': 'ایجاد فاکتور جدید',
                            'product_prices_json': _get_product_prices(), 'tax_percent': tax_percent,
                            'stock_errors': stock_errors,
                        })
                invoice.apply_product_inventory()
                messages.success(request, 'فاکتور با موفقیت ایجاد شد')
                return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
    return render(request, 'invoices/invoice_form.html', {
        'form': form, 'formset': formset, 'title': 'ایجاد فاکتور جدید',
        'product_prices_json': _get_product_prices(), 'tax_percent': tax_percent,
        'stock_errors': stock_errors,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.select_related('product').all()
    payment_form = PaymentForm()
    return render(request, 'invoices/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payment_form': payment_form,
    })


@login_required
def invoice_edit(request, pk):
    tax_percent = _get_tax_rate()
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == 'paid':
        messages.error(request, 'فاکتور پرداخت شده قابل ویرایش نیست')
        return redirect('invoice_detail', pk=pk)
    stock_errors = []
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid():
            # Reverse old inventory before changes
            invoice.reverse_product_inventory()
            invoice = form.save()
            if formset.is_valid():
                formset.save()
                invoice.calculate_totals()
                # Check stock if deduct_stock is checked
                if invoice.deduct_stock:
                    stock_errors = invoice.check_stock_availability()
                    if stock_errors:
                        messages.error(request, 'موجودی کافی نیست! لطفاً مقادیر را بررسی کنید.')
                        return render(request, 'invoices/invoice_form.html', {
                            'form': form, 'formset': formset, 'title': 'ویرایش فاکتور',
                            'invoice': invoice, 'product_prices_json': _get_product_prices(),
                            'tax_percent': tax_percent, 'stock_errors': stock_errors,
                        })
                invoice.apply_product_inventory()
                messages.success(request, 'فاکتور با موفقیت ویرایش شد')
                return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)
    return render(request, 'invoices/invoice_form.html', {
        'form': form, 'formset': formset, 'title': 'ویرایش فاکتور',
        'invoice': invoice, 'product_prices_json': _get_product_prices(),
        'tax_percent': tax_percent, 'stock_errors': stock_errors,
    })


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.reverse_product_inventory()
        invoice.delete()
        messages.success(request, 'فاکتور با موفقیت حذف شد')
        return redirect('invoice_list')
    return render(request, 'invoices/invoice_confirm_delete.html', {'object': invoice})


@login_required
def invoice_register_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            method = form.cleaned_data['method']
            invoice.register_payment(amount, method)
            messages.success(request, f'پرداخت {amount} ریال با موفقیت ثبت شد')
            return redirect('invoice_detail', pk=pk)
    return redirect('invoice_detail', pk=pk)


@login_required
def invoice_print_dark(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.select_related('product').all()
    return render(request, 'invoices/invoice_print_dark.html', {
        'invoice': invoice, 'items': items, 'company_info': _get_company_info(),
    })


@login_required
def invoice_print_light(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.select_related('product').all()
    return render(request, 'invoices/invoice_print_light.html', {
        'invoice': invoice, 'items': items, 'company_info': _get_company_info(),
    })

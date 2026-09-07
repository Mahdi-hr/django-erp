from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import SMSTemplate, SMSMessage, SMSProviderConfig
from .forms import SMSTemplateForm, SendSMSForm, SMSProviderConfigForm


@login_required
def sms_quick_settings(request):
    if request.method == 'POST':
        provider = request.POST.get('active_provider', 'demo')
        api_key = request.POST.get('api_key', '')
        sender_number = request.POST.get('sender_number', '')

        if provider != 'demo' and api_key and sender_number:
            config, _ = SMSProviderConfig.objects.update_or_create(
                provider=provider,
                defaults={
                    'api_key': api_key,
                    'sender_number': sender_number,
                    'is_active': True,
                }
            )
            SMSProviderConfig.objects.exclude(pk=config.pk).update(is_active=False)
            messages.success(request, f'تنظیمات {config.get_provider_display()} با موفقیت ذخیره شد')
        elif provider == 'demo':
            SMSProviderConfig.objects.update(is_active=False)
            messages.success(request, 'حالت تست فعال شد')
        else:
            messages.warning(request, 'لطفاً کلید API و شماره فرستنده را وارد کنید')

        return redirect('sms_dashboard')
    return redirect('sms_dashboard')


@login_required
def sms_dashboard(request):
    messages_list = SMSMessage.objects.select_related('customer')[:50]
    return render(request, 'sms/sms_dashboard.html', {'messages_list': messages_list})


@login_required
def template_list(request):
    templates = SMSTemplate.objects.all()
    return render(request, 'sms/template_list.html', {'templates': templates})


@login_required
def template_create(request):
    if request.method == 'POST':
        form = SMSTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'قالب با موفقیت ایجاد شد')
            return redirect('template_list')
    else:
        form = SMSTemplateForm()
    return render(request, 'sms/template_form.html', {'form': form, 'title': 'ایجاد قالب جدید'})


@login_required
def template_edit(request, pk):
    template = get_object_or_404(SMSTemplate, pk=pk)
    if request.method == 'POST':
        form = SMSTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'قالب با موفقیت ویرایش شد')
            return redirect('template_list')
    else:
        form = SMSTemplateForm(instance=template)
    return render(request, 'sms/template_form.html', {'form': form, 'title': 'ویرایش قالب'})


@login_required
def template_delete(request, pk):
    template = get_object_or_404(SMSTemplate, pk=pk)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'قالب با موفقیت حذف شد')
        return redirect('template_list')
    return render(request, 'sms/template_confirm_delete.html', {'object': template})


@login_required
def template_preview(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    template_id = request.POST.get('template_id')
    customer_id = request.POST.get('customer_id')
    try:
        tpl = SMSTemplate.objects.get(pk=template_id)
    except SMSTemplate.DoesNotExist:
        return JsonResponse({'error': 'قالب یافت نشد'}, status=404)

    context = {}
    if customer_id:
        from apps.customers.models import Customer
        try:
            c = Customer.objects.get(pk=customer_id)
            context = {
                'name': c.name or '',
                'company': c.company or '',
                'phone': c.phone or '',
            }
        except Customer.DoesNotExist:
            pass

    from django.conf import settings
    from django.utils import timezone
    import jdatetime
    context.setdefault('company_name', getattr(settings, 'COMPANY_NAME', 'شرکت'))
    context.setdefault('date', jdatetime.date.today().strftime('%Y/%m/%d'))
    context.setdefault('time', timezone.now().strftime('%H:%M'))

    rendered = tpl.render(**context)
    return JsonResponse({'rendered': rendered, 'body': tpl.body})


@login_required
def send_sms(request):
    if request.method == 'POST':
        form = SendSMSForm(request.POST)
        if form.is_valid():
            customer_ids = request.POST.getlist('customers')
            message_text = form.cleaned_data['message']
            template = form.cleaned_data.get('template')

            from apps.customers.models import Customer
            if customer_ids:
                customers = Customer.objects.filter(pk__in=customer_ids, is_active=True)
            else:
                customers = Customer.objects.none()

            if not customers.exists():
                messages.warning(request, 'لطفاً حداقل یک مشتری انتخاب کنید')
                return redirect('send_sms')

            from django.conf import settings
            from datetime import date
            company_name = getattr(settings, 'COMPANY_NAME', 'شرکت')
            today_str = date.today().strftime('%Y/%m/%d')

            sent_count = 0
            failed_count = 0
            from apps.sms.services import send_sms as do_send_sms
            for customer in customers:
                if not customer.phone:
                    continue
                personal_msg = message_text
                personal_msg = personal_msg.replace('{name}', customer.name or '')
                personal_msg = personal_msg.replace('{customer}', customer.name or '')
                personal_msg = personal_msg.replace('{phone}', customer.phone or '')
                personal_msg = personal_msg.replace('{company}', customer.company or '')
                personal_msg = personal_msg.replace('{company_name}', company_name)
                personal_msg = personal_msg.replace('{date}', today_str)

                try:
                    from apps.sms.tasks import send_sms_task
                    send_sms_task.delay(
                        customer.phone, personal_msg, 'demo',
                        customer.pk, template.pk if template else None,
                        request.user.pk
                    )
                except Exception:
                    status, msg_id = do_send_sms(customer.phone, personal_msg, 'demo')
                    SMSMessage.objects.create(
                        customer=customer, phone=customer.phone, message=personal_msg,
                        status=status, provider='demo',
                        provider_message_id=str(msg_id) if msg_id else '',
                        error_message='' if status == 'sent' else str(msg_id),
                        template=template,
                        sent_by=request.user,
                    )
                    if status == 'sent':
                        sent_count += 1
                    else:
                        failed_count += 1

            total = len([c for c in customers if c.phone])
            if failed_count:
                messages.warning(request, f'{sent_count} پیامک ارسال شد و {failed_count} ناموفق بود از {total} پیامک')
            else:
                messages.success(request, f'{total} پیامک در صف ارسال قرار گرفت')
            return redirect('sms_dashboard')
    else:
        form = SendSMSForm()
    templates_list = SMSTemplate.objects.filter(is_active=True)
    from apps.customers.models import Customer
    customers = Customer.objects.filter(is_active=True).order_by('name')
    return render(request, 'sms/send_sms.html', {
        'form': form,
        'title': 'ارسال پیامک',
        'templates_list': templates_list,
        'customers': customers,
    })


@login_required
@require_POST
def send_invoice_sms(request, invoice_pk):
    from apps.invoices.models import Invoice
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    customer = invoice.customer

    if not customer or not customer.phone:
        messages.warning(request, 'شماره تلفن مشتری ثبت نشده است')
        return redirect('invoice_detail', pk=invoice_pk)

    template_id = request.POST.get('template_id')
    message_text = request.POST.get('message', '')

    if template_id:
        try:
            tpl = SMSTemplate.objects.get(pk=template_id)
            message_text = tpl.render(
                name=customer.name or '',
                customer=customer.name or '',
                phone=customer.phone or '',
                company=customer.company or '',
                invoice_number=invoice.invoice_number or '',
                total=f'{int(invoice.total):,}',
                paid_amount=f'{int(invoice.paid_amount):,}',
                remaining=f'{int(invoice.remaining_amount):,}',
                status=invoice.get_status_display() or '',
                date=str(invoice.issue_date or ''),
            )
        except SMSTemplate.DoesNotExist:
            pass

    if not message_text:
        messages.warning(request, 'متن پیامک خالی است')
        return redirect('invoice_detail', pk=invoice_pk)

    try:
        from apps.sms.tasks import send_sms_task
        send_sms_task.delay(
            customer.phone, message_text, 'demo',
            customer.pk, int(template_id) if template_id else None,
            request.user.pk
        )
    except Exception:
        from apps.sms.services import send_sms as do_send_sms
        status, msg_id = do_send_sms(customer.phone, message_text, 'demo')
        SMSMessage.objects.create(
            customer=customer, invoice=invoice, phone=customer.phone,
            message=message_text, status=status, provider='demo',
            provider_message_id=str(msg_id) if msg_id else '',
            error_message='' if status == 'sent' else str(msg_id),
            sent_by=request.user,
        )

    messages.success(request, f'پیامک فاکتور {invoice.invoice_number} به {customer.phone} در صف ارسال قرار گرفت')
    return redirect('invoice_detail', pk=invoice_pk)


@login_required
def message_list(request):
    messages_list = SMSMessage.objects.select_related('customer', 'sent_by').all()

    # Date filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status_filter = request.GET.get('status', '')

    if date_from:
        messages_list = messages_list.filter(sent_at__date__gte=date_from)
    if date_to:
        messages_list = messages_list.filter(sent_at__date__lte=date_to)
    if status_filter:
        messages_list = messages_list.filter(status=status_filter)

    messages_list = messages_list[:200]  # limit to 200

    return render(request, 'sms/message_list.html', {
        'messages_list': messages_list,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
    })


@login_required
def delete_message(request, pk):
    msg = get_object_or_404(SMSMessage, pk=pk)
    msg.delete()
    messages.success(request, 'پیامک با موفقیت حذف شد')
    return redirect('message_list')


@login_required
def delete_all_messages(request):
    SMSMessage.objects.all().delete()
    messages.success(request, 'تمام پیامک‌ها با موفقیت حذف شدند')
    return redirect('message_list')


@login_required
def delete_messages_by_date(request):
    if request.method != 'POST':
        return redirect('message_list')
    date_from = request.POST.get('date_from', '')
    date_to = request.POST.get('date_to', '')
    status_filter = request.POST.get('status', '')

    qs = SMSMessage.objects.all()
    if date_from:
        qs = qs.filter(sent_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(sent_at__date__lte=date_to)
    if status_filter:
        qs = qs.filter(status=status_filter)

    count = qs.count()
    qs.delete()
    messages.success(request, f'{count} پیامک حذف شد')
    return redirect('message_list')


@login_required
def provider_config(request):
    configs = SMSProviderConfig.objects.all()
    return render(request, 'sms/provider_config.html', {'configs': configs})


@login_required
def provider_config_edit(request, pk):
    config = get_object_or_404(SMSProviderConfig, pk=pk)
    if request.method == 'POST':
        form = SMSProviderConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات با موفقیت ذخیره شد')
            return redirect('provider_config')
    else:
        form = SMSProviderConfigForm(instance=config)
    return render(request, 'sms/provider_config_form.html', {'form': form, 'title': 'ویرایش تنظیمات'})


@login_required
def test_provider_api(request, pk):
    config = get_object_or_404(SMSProviderConfig, pk=pk)
    if config.provider == 'smsir':
        from apps.sms.services import test_smsir_api
        success, result = test_smsir_api(config.api_key, config.sender_number)
    else:
        success, result = False, 'تست API برای این ارائه‌دهنده پشتیبانی نمی‌شود'
    if success:
        messages.success(request, f'تست موفق: {result}')
    else:
        messages.warning(request, f'تست ناموفق: {result}')
    return redirect('provider_config')


@login_required
def activate_provider(request, pk):
    config = get_object_or_404(SMSProviderConfig, pk=pk)
    SMSProviderConfig.objects.update(is_active=False)
    config.is_active = True
    config.save()
    messages.success(request, f'{config.get_provider_display()} به عنوان ارائه‌دهنده فعال انتخاب شد')
    return redirect('provider_config')


def _get_active_smsir():
    config = SMSProviderConfig.objects.filter(provider='smsir', is_active=True).first()
    if not config:
        return None
    try:
        from sms_ir import SmsIr
        return SmsIr(api_key=config.api_key, linenumber=config.sender_number)
    except Exception:
        return None


@login_required
def sms_report_today(request):
    result = None
    error = None
    sms = _get_active_smsir()
    if sms:
        try:
            result = sms.report_today(page_size=50, page_number=1)
        except Exception as e:
            error = str(e)
    else:
        error = 'ارائه‌دهنده SMS.ir فعال نیست'
    return render(request, 'sms/report_result.html', {
        'title': 'گزارش ارسال‌های امروز',
        'result': result,
        'error': error,
        'icon': 'calendar-day',
        'color': 'var(--accent)',
    })


@login_required
def sms_report_credit(request):
    result = None
    error = None
    sms = _get_active_smsir()
    if sms:
        try:
            result = sms.get_credit()
        except Exception as e:
            error = str(e)
    else:
        error = 'ارائه‌دهنده SMS.ir فعال نیست'
    return render(request, 'sms/report_result.html', {
        'title': 'گزارش اعتبار حساب',
        'result': result,
        'error': error,
        'icon': 'wallet',
        'color': 'var(--success)',
    })


@login_required
def sms_report_lines(request):
    result = None
    error = None
    sms = _get_active_smsir()
    if sms:
        try:
            result = sms.get_line_numbers()
        except Exception as e:
            error = str(e)
    else:
        error = 'ارائه‌دهنده SMS.ir فعال نیست'
    return render(request, 'sms/report_result.html', {
        'title': 'گزارش شماره خطوط',
        'result': result,
        'error': error,
        'icon': 'hashtag',
        'color': 'var(--info)',
    })


@login_required
def sms_report_received(request):
    result = None
    error = None
    sms = _get_active_smsir()
    if sms:
        try:
            result = sms.report_latest_received(count=50)
        except Exception as e:
            error = str(e)
    else:
        error = 'ارائه‌دهنده SMS.ir فعال نیست'
    return render(request, 'sms/report_result.html', {
        'title': 'گزارش پیامک‌های دریافتی',
        'result': result,
        'error': error,
        'icon': 'inbox',
        'color': 'var(--warning)',
    })

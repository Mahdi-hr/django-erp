from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SMSTemplate, SMSMessage, SMSProviderConfig
from .forms import SMSTemplateForm, SendSMSForm, BulkSMSForm, SMSProviderConfigForm


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
def send_sms(request):
    if request.method == 'POST':
        form = SendSMSForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            message_text = form.cleaned_data['message']
            template = form.cleaned_data.get('template')
            try:
                from apps.sms.tasks import send_sms_task
                send_sms_task.delay(phone, message_text, 'demo', None, template.pk if template else None, request.user.pk)
                messages.success(request, 'پیامک در صف ارسال قرار گرفت')
            except Exception:
                from apps.sms.services import send_sms as do_send_sms
                status, msg_id = do_send_sms(phone, message_text, 'demo')
                SMSMessage.objects.create(
                    phone=phone, message=message_text, status=status,
                    provider='demo', provider_message_id=str(msg_id) if msg_id else '',
                    error_message='' if status == 'sent' else str(msg_id),
                    sent_by=request.user,
                )
                if status == 'sent':
                    messages.success(request, 'پیامک با موفقیت ارسال شد')
                else:
                    messages.warning(request, f'خطا در ارسال: {msg_id}')
            return redirect('sms_dashboard')
    else:
        form = SendSMSForm()
    templates_list = SMSTemplate.objects.filter(is_active=True)
    return render(request, 'sms/send_sms.html', {'form': form, 'title': 'ارسال پیامک', 'templates_list': templates_list})


@login_required
def send_bulk_sms(request):
    if request.method == 'POST':
        message_text = request.POST.get('message', '')
        customer_ids = request.POST.getlist('customers')
        from apps.customers.models import Customer
        customers = Customer.objects.filter(pk__in=customer_ids, is_active=True)
        from django.conf import settings
        company_name = getattr(settings, 'COMPANY_NAME', 'شرکت')
        from datetime import date
        today_str = date.today().strftime('%Y/%m/%d')

        sent_count = 0
        from apps.sms.services import send_sms as do_send_sms
        for customer in customers:
            if not customer.phone:
                continue
            personal_msg = message_text
            personal_msg = personal_msg.replace('{customer}', customer.name or '')
            personal_msg = personal_msg.replace('{phone}', customer.phone or '')
            personal_msg = personal_msg.replace('{company}', company_name)
            personal_msg = personal_msg.replace('{date}', today_str)
            status, msg_id = do_send_sms(customer.phone, personal_msg, 'demo')
            SMSMessage.objects.create(
                customer=customer, phone=customer.phone, message=personal_msg,
                status=status, provider='demo',
                provider_message_id=str(msg_id) if msg_id else '',
                error_message='' if status == 'sent' else str(msg_id),
                sent_by=request.user,
            )
            if status == 'sent':
                sent_count += 1
        messages.success(request, f'{sent_count} پیامک ارسال شد از {len(customers)} پیامک')
        return redirect('sms_dashboard')
    from apps.customers.models import Customer
    customers = Customer.objects.filter(is_active=True, phone__isnull=False).exclude(phone='')
    templates_list = SMSTemplate.objects.filter(is_active=True)
    return render(request, 'sms/send_bulk_sms.html', {'title': 'ارسال پیامک گروهی', 'customers': customers, 'templates_list': templates_list})


@login_required
def message_list(request):
    messages_list = SMSMessage.objects.select_related('customer', 'sent_by').all()
    return render(request, 'sms/message_list.html', {'messages_list': messages_list})


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

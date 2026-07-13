import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from apps.common.models import Setting
from apps.settings_app.models import FixedCost


THEME_DEFAULTS = {
    'theme_bg_body': '#1e2a3a',
    'theme_bg_card': '#2a3a52',
    'theme_bg_sidebar': '#162033',
    'theme_bg_table_row': '#2a3a52',
    'theme_bg_input': '#2a3a52',
    'theme_accent': '#6366f1',
    'theme_accent_light': '#818cf8',
    'theme_success': '#10b981',
    'theme_danger': '#ef4444',
    'theme_warning': '#f59e0b',
    'theme_info': '#06b6d4',
    'theme_text_primary': '#e8edf5',
    'theme_text_secondary': '#b0bec5',
    'theme_sidebar_style': 'gradient',
    'theme_card_radius': '16',
    'theme_card_blur': '12',
    'theme_font_size': '14',
}


@login_required
def settings_dashboard(request):
    active_tab = request.GET.get('tab', 'general')

    # Handle general settings form submission
    if request.method == 'POST' and not request.POST.get('tab'):
        for key, val in request.POST.items():
            if key in ('csrfmiddlewaretoken', 'tab', 'company_logo_delete'):
                continue
            # Convert percentage to multiplier for price multiplier fields
            if 'multiplier' in key:
                try:
                    val = str(float(val) / 100)
                except (ValueError, ZeroDivisionError):
                    pass
            Setting.set_value(key, val, category='general')

        # Handle logo file upload
        logo_file = request.FILES.get('company_logo_file')
        if logo_file:
            # Delete old logo file if exists
            old_logo = Setting.get_value('company_logo', '')
            if old_logo and not old_logo.startswith('fa-'):
                old_path = os.path.join('logos', old_logo)
                if default_storage.exists(old_path):
                    default_storage.delete(old_path)

            # Save new logo
            ext = os.path.splitext(logo_file.name)[1].lower()
            filename = f'company_logo{ext}'
            filepath = os.path.join('logos', filename)
            default_storage.save(filepath, logo_file)
            Setting.set_value('company_logo', filename, category='general')

        # Handle logo deletion
        if request.POST.get('company_logo_delete'):
            old_logo = Setting.get_value('company_logo', '')
            if old_logo and not old_logo.startswith('fa-'):
                old_path = os.path.join('logos', old_logo)
                if default_storage.exists(old_path):
                    default_storage.delete(old_path)
            Setting.set_value('company_logo', '', category='general')

        # Cascade multiplier/profit changes to all products
        from apps.products.services import recalculate_all_products
        recalculate_all_products()

        messages.success(request, 'تنظیمات با موفقیت ذخیره شد')
        return redirect('settings_dashboard')

    # Handle theme form submission
    if request.method == 'POST' and request.POST.get('tab') == 'theme':
        for key in THEME_DEFAULTS:
            val = request.POST.get(key, THEME_DEFAULTS[key])
            Setting.set_value(key, val, category='theme')
        messages.success(request, 'تنظیمات ظاهر با موفقیت ذخیره شد')
        return redirect('settings_dashboard')

    settings = Setting.objects.all()
    fixed_costs = FixedCost.objects.all()

    theme = {}
    for key, default in THEME_DEFAULTS.items():
        theme[key] = Setting.get_value(key, default)

    # Check if company_logo is an image path or a FontAwesome icon
    logo_val = Setting.get_value('company_logo', '')
    company_logo_path = '' if logo_val.startswith('fa-') or not logo_val else logo_val

    return render(request, 'settings_app/settings_dashboard.html', {
        'settings': settings,
        'fixed_costs': fixed_costs,
        'active_tab': active_tab,
        'theme': theme,
        'company_logo_path': company_logo_path,
        'MEDIA_URL': '/media/',
    })


@login_required
def setting_edit(request, pk):
    setting = Setting.objects.get(pk=pk)
    if request.method == 'POST':
        setting.value = request.POST.get('value', setting.value)
        setting.save()
        messages.success(request, 'تنظیم با موفقیت ذخیره شد')
        return redirect('settings_dashboard')
    return render(request, 'settings_app/setting_edit.html', {'setting': setting})


@login_required
def fixed_cost_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', 0)
        category = request.POST.get('category', '')
        FixedCost.objects.create(name=name, amount=amount, category=category)
        messages.success(request, 'هزینه ثابت با موفقیت ایجاد شد')
        return redirect('settings_dashboard')
    return render(request, 'settings_app/fixed_cost_form.html', {'title': 'ایجاد هزینه ثابت'})


@login_required
def fixed_cost_edit(request, pk):
    fc = FixedCost.objects.get(pk=pk)
    if request.method == 'POST':
        fc.name = request.POST.get('name', fc.name)
        fc.amount = request.POST.get('amount', fc.amount)
        fc.category = request.POST.get('category', fc.category)
        fc.is_active = 'is_active' in request.POST
        fc.save()
        messages.success(request, 'هزینه ثابت با موفقیت ویرایش شد')
        return redirect('settings_dashboard')
    return render(request, 'settings_app/fixed_cost_form.html', {'fc': fc, 'title': 'ویرایش هزینه ثابت'})


@login_required
def fixed_cost_delete(request, pk):
    fc = FixedCost.objects.get(pk=pk)
    if request.method == 'POST':
        fc.delete()
        messages.success(request, 'هزینه ثابت حذف شد')
        return redirect('settings_dashboard')
    return render(request, 'settings_app/fixed_cost_confirm_delete.html', {'object': fc})


@login_required
def theme_customizer(request):
    return redirect('settings_dashboard')


@login_required
def theme_save_ajax(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        for key, val in data.items():
            if key.startswith('theme_'):
                Setting.set_value(key, val, category='theme')
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

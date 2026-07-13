import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import UpdateLog, VersionManager


@login_required
@staff_member_required
def updater_dashboard(request):
    """داشبورد آپدیت"""
    version_info = VersionManager.get_version_info()
    update_check = VersionManager.check_remote_updates()
    recent_logs = UpdateLog.objects.all()[:10]
    backups = VersionManager.get_backups()[:5]

    context = {
        'version_info': version_info,
        'update_check': update_check,
        'recent_logs': recent_logs,
        'backups': backups,
        'active_tab': 'updater',
    }
    return render(request, 'updater/dashboard.html', context)


@login_required
@staff_member_required
@require_POST
def check_updates(request):
    """بررسی آپدیت"""
    update_check = VersionManager.check_remote_updates()
    return JsonResponse(update_check)


@login_required
@staff_member_required
@require_POST
def perform_update(request):
    """اجرای آپدیت"""
    try:
        # دریافت تأیید کاربر
        confirm = request.POST.get('confirm')
        if confirm != 'yes':
            return JsonResponse({
                'success': False,
                'error': 'آپدیت تأیید نشد'
            })

        # اجرای آپدیت
        result = VersionManager.perform_update(user=request.user)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@staff_member_required
@require_POST
def rollback_update(request):
    """بازگشت به نسخه قبلی"""
    backup_path = request.POST.get('backup_path')
    if not backup_path:
        return JsonResponse({
            'success': False,
            'error': 'مسیر بک‌آپ مشخص نشده'
        })

    try:
        VersionManager.rollback(backup_path)
        messages.success(request, 'بازگشت با موفقیت انجام شد')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@staff_member_required
def version_history(request):
    """تاریخخچه آپدیت‌ها"""
    logs = UpdateLog.objects.all()
    return render(request, 'updater/history.html', {'logs': logs})


@login_required
@staff_member_required
def backup_list(request):
    """لیست بک‌آپ‌ها"""
    backups = VersionManager.get_backups()
    return render(request, 'updater/backups.html', {'backups': backups})

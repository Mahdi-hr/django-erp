from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification


@login_required
def mark_all_notifications_read(request):
    if request.method == 'GET':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'همه اعلانات خوانده شد')
    return redirect(request.META.get('HTTP_REFERER', '/'))

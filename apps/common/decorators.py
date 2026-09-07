from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(*allowed_roles):
    """
    Decorator that checks user role before allowing access.
    Usage: @role_required('admin', 'warehouse')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role == 'admin' or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'شما دسترسی به این بخش را ندارید')
            return redirect('dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Only admin users can access."""
    return role_required('admin')(view_func)


def accountant_required(view_func):
    """Only accountant and admin users can access."""
    return role_required('admin', 'accountant')(view_func)


def warehouse_required(view_func):
    """Only warehouse and admin users can access."""
    return role_required('admin', 'warehouse')(view_func)


def operator_required(view_func):
    """Only operator and admin users can access."""
    return role_required('admin', 'operator')(view_func)

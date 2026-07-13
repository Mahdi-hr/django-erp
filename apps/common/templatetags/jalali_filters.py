from django import template
from django.utils.safestring import mark_safe
import jdatetime

register = template.Library()


@register.filter(name='to_jalali')
def to_jalali(value):
    if not value:
        return ''
    try:
        if hasattr(value, 'date'):
            value = value.date()
        jalali_date = jdatetime.date.fromgregorian(date=value)
        return jalali_date.strftime('%Y/%m/%d')
    except (ValueError, AttributeError):
        return str(value)


@register.filter(name='to_jalali_datetime')
def to_jalali_datetime(value):
    if not value:
        return ''
    try:
        jalali_datetime = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_datetime.strftime('%Y/%m/%d %H:%M')
    except (ValueError, AttributeError):
        return str(value)


@register.filter(name='currency_format')
def currency_format(value):
    if value is None:
        return '0'
    try:
        return f'{int(value):,}'
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='to_percent')
def to_percent(value):
    try:
        return round(float(value) * 100, 1)
    except (ValueError, TypeError):
        return value


@register.simple_tag
def has_permission(user, permission):
    return user.has_permission(permission)


@register.inclusion_tag('includes/sidebar.html', takes_context=True)
def render_sidebar(context):
    return {
        'user': context.get('user'),
        'request': context.get('request'),
    }

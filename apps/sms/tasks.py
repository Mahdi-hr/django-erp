from celery import shared_task
from django.utils import timezone


@shared_task
def send_sms_task(phone, message, provider=None, customer_id=None, template_id=None, sent_by_id=None):
    from apps.sms.services import send_sms
    from apps.sms.models import SMSMessage
    from apps.customers.models import Customer

    status, msg_id = send_sms(phone, message, provider)

    customer = None
    if customer_id:
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            pass

    SMSMessage.objects.create(
        customer=customer,
        template_id=template_id,
        phone=phone,
        message=message,
        status=status,
        provider=provider or 'demo',
        provider_message_id=msg_id if isinstance(msg_id, str) else '',
        error_message='' if status == 'sent' else str(msg_id),
        sent_by_id=sent_by_id,
    )
    return status


@shared_task
def send_bulk_sms(phone_numbers, message, provider=None, sent_by_id=None):
    from apps.sms.services import send_sms
    from apps.sms.models import SMSMessage

    results = []
    for phone, customer_id in phone_numbers:
        status, msg_id = send_sms(phone, message, provider)
        SMSMessage.objects.create(
            customer_id=customer_id,
            phone=phone,
            message=message,
            status=status,
            provider=provider or 'demo',
            provider_message_id=msg_id if isinstance(msg_id, str) else '',
            error_message='' if status == 'sent' else str(msg_id),
            sent_by_id=sent_by_id,
        )
        results.append({'phone': phone, 'status': status})
    return results

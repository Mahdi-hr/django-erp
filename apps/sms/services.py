import requests
from django.conf import settings


def send_kavenegar(phone, message):
    config = _get_provider_config('kavenegar')
    if not config:
        return False, 'تنظیمات کاوه‌نگار یافت نشد'
    try:
        url = f'https://api.kavenegar.com/v1/{config.api_key}/sms/send.json'
        response = requests.post(url, data={
            'receptor': phone,
            'message': message,
            'sender': config.sender_number,
        }, timeout=30)
        data = response.json()
        if response.status_code == 200 and data.get('return', {}).get('status') == 200:
            return True, data['result'][0].get('messageid', '')
        return False, str(data)
    except Exception as e:
        return False, str(e)


def send_smsir(phone, message):
    config = _get_provider_config('smsir')
    if not config:
        return False, 'تنظیمات SMS.ir یافت نشد'
    try:
        from sms_ir import SmsIr
        sms = SmsIr(api_key=config.api_key, linenumber=config.sender_number)
        response = sms.send_sms(number=phone, message=message, linenumber=config.sender_number)
        if hasattr(response, 'status') and response.status == 1:
            return True, str(getattr(response, 'message_id', ''))
        elif isinstance(response, dict):
            if response.get('status') == 1:
                return True, str(response.get('message_id', ''))
            return False, response.get('message', str(response))
        return True, str(response)
    except Exception as e:
        return False, str(e)


def test_smsir_api(api_key, linenumber):
    try:
        from sms_ir import SmsIr
        sms = SmsIr(api_key=api_key, linenumber=linenumber)
        credit = sms.get_credit()
        if hasattr(credit, 'Credit'):
            return True, f'اعتبار حساب: {credit.Credit}'
        elif isinstance(credit, dict):
            return True, f'اعتبار حساب: {credit.get("Credit", credit)}'
        return True, f'پاسخ: {credit}'
    except Exception as e:
        return False, str(e)


def send_sms(phone, message, provider=None):
    if provider is None:
        config = _get_provider_config_active()
        if config:
            provider = config.provider
        else:
            provider = 'demo'
    if provider == 'kavenegar':
        success, msg_id = send_kavenegar(phone, message)
    elif provider == 'smsir':
        success, msg_id = send_smsir(phone, message)
    else:
        success, msg_id = True, 'demo-message-id'
    status = 'sent' if success else 'failed'
    return status, msg_id


def _get_provider_config(provider):
    from apps.sms.models import SMSProviderConfig
    try:
        return SMSProviderConfig.objects.get(provider=provider, is_active=True)
    except SMSProviderConfig.DoesNotExist:
        return None


def _get_provider_config_active():
    from apps.sms.models import SMSProviderConfig
    return SMSProviderConfig.objects.filter(is_active=True).first()

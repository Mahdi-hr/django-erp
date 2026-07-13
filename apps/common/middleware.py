import time
from django.core.cache import cache
from django.http import JsonResponse


class RateLimitMiddleware:
    RATE_LIMIT = 100
    WINDOW = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            ip = self.get_client_ip(request)
            cache_key = f'ratelimit:{ip}'
            request_count = cache.get(cache_key, 0)

            if request_count >= self.RATE_LIMIT:
                return JsonResponse({'error': 'تعداد درخواست‌ها بیش از حد مجاز است'}, status=429)

            cache.set(cache_key, request_count + 1, self.WINDOW)
        except Exception:
            pass

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

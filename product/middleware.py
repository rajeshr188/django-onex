from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from .models import Rate

# in case the rate needs tobe in cache
class RateMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rate = cache.get('latest_rate')
        if not rate:
            rate = Rate.objects.latest('date')
            cache.set('latest_rate', rate)
        request.rate = rate

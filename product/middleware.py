from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

from .models import Rate


# in case the rate needs tobe in cache
class RateMiddleware(MiddlewareMixin):
    def process_request(self, request):
        grate = cache.get("latest_gold_rate")
        srate = cache.get("latest_silver_rate")

        if not (grate and srate):
            grate = Rate.objects.filter(metal=Rate.Metal.GOLD).latest("timestamp")
            srate = Rate.objects.filter(metal=Rate.Metal.SILVER).latest("timestamp")

            cache.set("latest_gold_rate", grate)
            cache.set("latest_silver_rate", srate)
        request.grate = grate
        request.srate = srate

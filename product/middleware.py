from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils.deprecation import MiddlewareMixin

from .models import Rate


# in case the rate needs tobe in cache
class RateMiddleware(MiddlewareMixin):
    def process_request(self, request):
        grate = cache.get("latest_gold_rate")
        srate = cache.get("latest_silver_rate")

        if not grate:
            try:
                grate = Rate.objects.filter(metal=Rate.Metal.GOLD).latest("timestamp")
                cache.set("latest_gold_rate", grate)
            except ObjectDoesNotExist:
                grate = None
        request.grate = grate

        if not srate:
            try:
                srate = Rate.objects.filter(metal=Rate.Metal.SILVER).latest("timestamp")
                cache.set("latest_silver_rate", srate)
            except ObjectDoesNotExist:
                srate = None
        request.srate = srate

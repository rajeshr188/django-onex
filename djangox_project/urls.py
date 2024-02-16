from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

# from controlcenter.views import controlcenter
urlpatterns = [
    path("admin/", admin.site.urls),
    path("invitations/", include("invitations.urls", namespace="invitations")),
    path("activity/", include("actstream.urls")),
    path("dynamic_preferences/", include("dynamic_preferences.urls")),
    path("users/", include("django.contrib.auth.urls")),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("allauth.socialaccount.urls")),
    path("", include("pages.urls")),
    path("approval/", include("approval.urls", namespace="approval")),
    path("contact/", include("contact.urls")),
    path("product/", include("product.urls")),
    path("girvi/", include("girvi.urls")),
    path("sales/", include("sales.urls", namespace="sales")),
    path("chitfund/", include("Chitfund.urls")),
    path("purchase/", include("purchase.urls", namespace="purchase")),
    path("daybook/", include("daybook.urls")),
    path("dea/", include("dea.urls")),
    path("sea/", include("sea.urls")),
    path("notify/", include("notify.urls")),
    path("select2/", include("django_select2.urls")),
    path("rates/", include("rates.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

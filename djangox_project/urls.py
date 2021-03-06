from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from controlcenter.views import controlcenter
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('pages.urls')),
    path('approval/',include('approval.urls')),
    path('contact/',include('contact.urls')),
    path('product/',include('product.urls')),
    path('girvi/',include('girvi.urls')),
    path('sales/',include('sales.urls')),
    path('chitfund/',include('Chitfund.urls')),
    path('purchase/',include('purchase.urls')),
    path('daybook/',include('daybook.urls')),
    path('ledger/',include('ledger.urls')),
    path('select2/', include('django_select2.urls')),
    # path('admin/dashboard/',controlcenter.urls),
    # path('silk/',include('silk.urls',namespace='silk')),
    path('api-auth/',include('rest_framework.urls')),
    path('activity/',include('actstream.urls')),

]

if settings.DEBUG:
    urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

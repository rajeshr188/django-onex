from django.urls import path
from .views import get_latest_rate,rate_list, rate_detail, rate_create, rate_update, rate_delete, ratesource_list, ratesource_detail, ratesource_create,ratesource_update, ratesource_delete

urlpatterns = [
    path(
        "rates/latest/",
        get_latest_rate,
        name="historical_rate",
    ),
    path('rates/', rate_list, name='rate_list'),
    path('rates/<int:pk>/', rate_detail, name='rate_detail'),
    path('rates/new/', rate_create, name='rate_create'),
    path('rates/<int:pk>/edit/', rate_update, name='rate_update'),
    path('rates/<int:pk>/delete/', rate_delete, name='rate_delete'),
    path('ratesources/', ratesource_list, name='ratesource_list'),
    path('ratesources/<int:pk>/', ratesource_detail, name='ratesource_detail'),
    path('ratesources/new/', ratesource_create, name='ratesource_create'),
    path('ratesources/<int:pk>/edit/', ratesource_update, name='ratesource_update'),
    path('ratesources/<int:pk>/delete/', ratesource_delete, name='ratesource_delete'),
    
]

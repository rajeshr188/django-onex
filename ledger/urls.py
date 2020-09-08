from django.urls import path, include
from . import views

urlpatterns = (
    # urls for Ledger
    path('ledger/',views.home,name='ledger_home'),
)

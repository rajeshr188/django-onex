from sea.views import acc_summary
from django.urls import path
from .import views
urlpatterns = [
    path('acc_summary/',views.acc_summary,name='acc_summary')
]

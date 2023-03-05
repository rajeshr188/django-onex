from django.urls import path

from sea.views import acc_summary

from . import views

urlpatterns = [path("acc_summary/", views.acc_summary, name="acc_summary")]

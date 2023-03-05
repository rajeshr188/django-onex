from django.urls import include, path

from . import views

urlpatterns = (
    # urls for Customer
    path("daybook/", views.daybook, name="daybook"),
)

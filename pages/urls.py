from django.urls import path

from .views import AboutPageView, Dashboard, HomePageView

urlpatterns = [
    path("", HomePageView, name="home"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("dashboard/", Dashboard, name="dashboard"),
]

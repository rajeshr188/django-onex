from django.urls import path

from .views import *

urlpatterns = [
    path("", HomePageView, name="home"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("dashboard/", Dashboard, name="dashboard"),
    path("privacypolicy/", PrivacyPolicy.as_view(), name="privacypolicy"),
    path("termsandconditions/", TermsAndConditions.as_view(), name="termsandconditions"),
]

from django.urls import include, path
from rest_framework import routers

from . import api, views

router = routers.DefaultRouter()
router.register(r"customer", api.CustomerViewSet)

urlpatterns = (
    # urls for Django Rest Framework API
    path("api/v1/", include(router.urls)),
)

urlpatterns += (
    # urls for Customer
    path("", views.home, name="contact_home"),
    path("customer/", views.customer_list, name="contact_customer_list"),
    path("customer/create/", views.customer_create, name="contact_customer_create"),
    path(
        "customer/detail/<int:pk>/",
        views.customer_detail,
        name="contact_customer_detail",
    ),
    path(
        "customer/update/<int:pk>/", views.customer_edit, name="contact_customer_update"
    ),
    path(
        "customer/<int:pk>/delete/",
        views.customer_delete,
        name="contact_customer_delete",
    ),
    path(
        "customer/<int:pk>/reallot_receipts/",
        views.reallot_receipts,
        name="contact_reallot_receipts",
    ),
    path(
        "customer/<int:pk>/reallot_payments/",
        views.reallot_payments,
        name="contact_reallot_payments",
    ),
    path(
        "customer/<int:pk>/contactno/add/",
        views.contact_create,
        name="customer_contact_form",
    ),
    path(
        "customer/contactno/<int:pk>/detail/",
        views.contact_detail,
        name="customer_contact_detail",
    ),
    path(
        "customer/contactno/<int:pk>/edit/",
        views.contact_update,
        name="customer_contact_update",
    ),
    path(
        "customer/contactno/<int:pk>/delete/",
        views.contact_delete,
        name="customer_contact_delete",
    ),
    path(
        "customer/<int:pk>/contactno/",
        views.contact_list,
        name="customer_contactno_list",
    ),
    path(
        "customer/<int:pk>/address/",
        views.address_list,
        name="customer_address_list",
    ),
    path(
        "customer/<int:pk>/address/add/",
        views.address_create,
        name="customer_address_form",
    ),
    path(
        "customer/address/<int:pk>/detail/",
        views.address_detail,
        name="customer_address_detail",
    ),
    path(
        "customer/address/<int:pk>/edit/",
        views.address_update,
        name="customer_address_update",
    ),
    path(
        "customer/address/<int:pk>/delete/",
        views.address_delete,
        name="customer_address_delete",
    ),
    path("customer/merge/", views.customer_merge, name="contact_customer_merge"),
)

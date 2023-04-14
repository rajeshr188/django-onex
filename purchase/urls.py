from django.urls import include, path
from rest_framework import routers

from . import api, views

router = routers.DefaultRouter()
router.register(r"invoice", api.InvoiceViewSet)
router.register(r"invoiceitem", api.InvoiceItemViewSet)
router.register(r"payment", api.PaymentViewSet)

app_name = "purchase"

urlpatterns = (
    # urls for Django Rest Framework API
    path("api/v1/", include(router.urls)),
)

urlpatterns += (
    # urls for Invoice
    # path('home/',views.home,name = 'purchase_home'),
    path("list/", views.purchase_list, name="purchase_invoice_list"),
    path("create/", views.purchase_create, name="purchase_invoice_create"),
    path(
        "<int:pk>/detail/", views.purchase_detail_view, name="purchase_invoice_detail"
    ),
    path("<int:id>/update/", views.purchase_update, name="purchase_invoice_update"),
    path(
        "<int:id>/delete/", views.purchase_delete_view, name="purchase_invoice_delete"
    ),
)
urlpatterns += (
    # path('purchase/balance/',views.list_balance,name='purchase_balance'),
)
urlpatterns += (
    # urls for InvoiceItem
    path(
        "purchase/product/price/history", views.get_product_price, name="price_history"
    ),
    path(
        "<int:parent_id>/invoiceitem/create/",
        views.purchase_item_update_hx_view,
        name="purchase_invoiceitem_create",
    ),
    path(
        "<int:parent_id>/invoiceitem/detail/<int:id>/",
        views.purchase_item_update_hx_view,
        name="purchase_invoiceitem_detail",
    ),
    path(
        "<int:parent_id>/invoiceitem/delete/<int:id>/",
        views.purchase_item_delete_view,
        name="purchase_invoiceitem_delete",
    ),
)

urlpatterns += (
    # urls for Payment
    path(
        "purchase/payment/",
        views.payment_list,
        name="purchase_payment_list",
    ),
    path(
        "purchase/payment/create/",
        views.payment_create,
        name="purchase_payment_create",
    ),
    path(
        "purchase/payment/detail/<int:pk>/",
        views.payment_detail,
        name="purchase_payment_detail",
    ),
    path(
        "purchase/payment/update/<int:pk>/",
        views.payment_update,
        name="purchase_payment_update",
    ),
    path(
        "purchase/payment/delete/<int:pk>/",
        views.payment_delete,
        name="purchase_payment_delete",
    ),
    path(
        "purchase/payment/<int:pk>/allocate/",
        views.payment_allocate,
        name="purchase_payment_allocate",
    ),
)

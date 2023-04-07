from django.urls import include, path
from rest_framework import routers

from . import api, views

router = routers.DefaultRouter()
router.register(r"invoice", api.InvoiceViewSet)
router.register(r"invoiceitem", api.InvoiceItemViewSet)
router.register(r"receipt", api.ReceiptViewSet)

app_name = "sales"

urlpatterns = (
    # urls for Django Rest Framework API
    path("api/v1/", include(router.urls)),
)

urlpatterns += (
    # urls for Invoice
    path("sales/invoice/", views.sales_list, name="sales_invoice_list"),
    path("sales/invoice/create/", views.sale_create_view, name="sales_invoice_create"),
    path(
        "sales/detail/<int:pk>/", views.sales_detail_view, name="sales_invoice_detail"
    ),
    path("hx/detail/<int:id>/", views.sales_detail_hx_view, name="hx-detail"),
    # path(
    #     "sales/invoice/detail/<int:pk>/pdf",
    #     views.print_invoice,
    #     name="sales_invoicepdf",
    # ),
    path(
        "sales/invoice/update/<int:id>/",
        views.sale_update_view,
        name="sales_invoice_update",
    ),
    path(
        "sales/invoice/delete/<int:id>/",
        views.sales_delete_view,
        name="sales_invoice_delete",
    ),
    path("sales/invoice/<int:pk>/post/", views.post_sales, name="sales_invoice_post"),
    path(
        "sales/invoice/<int:pk>/unpost/",
        views.unpost_sales,
        name="sales_invoice_unpost",
    ),
)
urlpatterns += (
    path("sales/", views.home, name="sales_home"),
    path("sales/upload/", views.simple_upload, name="simpleupload"),
    # path('sales/balance/',views.list_balance,name='sales_balance'),
)
urlpatterns += (
    # urls for InvoiceItem
    path("sales/product/price", views.get_sale_price, name="sale_product_price"),
    path(
        "sales/<int:parent_id>/invoiceitem/create",
        views.sale_item_update_hx_view,
        name="sales_invoiceitem_create",
    ),
    path(
        "sales/<int:parent_id>/invoiceitem/<int:id>/",
        views.sale_item_update_hx_view,
        name="hx-invoiceitem-detail",
    ),
    path(
        "sales/<int:parent_id>/invoiceitem/<int:id>/delete/",
        views.sale_item_delete_view,
        name="sales_invoiceitem_delete",
    ),
)

urlpatterns += (
    # urls for Receipt
    path("sales/receipt/", views.ReceiptListView.as_view(), name="sales_receipt_list"),
    path(
        "sales/receipt/create/",
        views.ReceiptCreateView.as_view(),
        name="sales_receipt_create",
    ),
    path(
        "sales/receipt/detail/<int:pk>/",
        views.ReceiptDetailView.as_view(),
        name="sales_receipt_detail",
    ),
    # path("sales/receipt/detail/<int:pk>/pdf", views.print_receipt, name="receiptpdf"),
    path(
        "sales/receipt/update/<int:pk>/",
        views.ReceiptUpdateView.as_view(),
        name="sales_receipt_update",
    ),
    path(
        "sales/receipt/delete/<int:pk>/",
        views.ReceiptDeleteView.as_view(),
        name="sales_receipt_delete",
    ),
    path("sales/receipt/<int:pk>/post/", views.post_receipt, name="sales_receipt_post"),
    path(
        "sales/receipt/<int:pk>/unpost/",
        views.unpost_receipt,
        name="sales_receipt_unpost",
    ),
    path(
        "sales/receipt/<int:pk>/allocate/",
        views.receipt_allocate,
        name="sales_receipt_allocate",
    ),
)

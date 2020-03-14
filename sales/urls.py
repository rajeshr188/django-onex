from django.urls import path, include
from rest_framework import routers

from . import api
from . import views

router = routers.DefaultRouter()
router.register(r'invoice', api.InvoiceViewSet)
router.register(r'invoiceitem', api.InvoiceItemViewSet)
router.register(r'receipt', api.ReceiptViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Invoice
    path('sales/invoice/', views.InvoiceListView.as_view(), name='sales_invoice_list'),
    path('sales/invoice/create/', views.InvoiceCreateView.as_view(), name='sales_invoice_create'),
    path('sales/invoice/detail/<int:pk>/', views.InvoiceDetailView.as_view(), name='sales_invoice_detail'),
    path('sales/invoice/detail/<int:pk>/pdf', views.print_invoice,name='sales_invoicepdf'),
    path('sales/invoice/update/<int:pk>/', views.InvoiceUpdateView.as_view(), name='sales_invoice_update'),
    path('sales/invoice/delete/<int:pk>/', views.InvoiceDeleteView.as_view(), name='sales_invoice_delete'),
)
urlpatterns+=(
            path('sales/',views.home,name='sales_home'),
            path('sales/randomsales/',views.randomsales,name='randomsales'),
            path('sales/upload/',views.simple_upload,name='simpleupload'),
            path('sales/balance/',views.list_balance,name='sales_balance'),
            path('sales/graph/',views.graph,name='graph'),
            path('sales/sales_count_by_month/',views.sales_count_by_month,name='sales_count_by_month'),
            )
urlpatterns += (
    # urls for InvoiceItem
    path('sales/invoiceitem/', views.InvoiceItemListView.as_view(), name='sales_invoiceitem_list'),
    path('sales/invoiceitem/create/', views.InvoiceItemCreateView.as_view(), name='sales_invoiceitem_create'),
    path('sales/invoiceitem/detail/<int:pk>/', views.InvoiceItemDetailView.as_view(), name='sales_invoiceitem_detail'),
    path('sales/invoiceitem/update/<int:pk>/', views.InvoiceItemUpdateView.as_view(), name='sales_invoiceitem_update'),
)

urlpatterns += (
    # urls for Receipt
    path('sales/receipt/', views.ReceiptListView.as_view(), name='sales_receipt_list'),
    path('sales/receipt/create/', views.ReceiptCreateView.as_view(), name='sales_receipt_create'),
    path('sales/receipt/detail/<int:pk>/', views.ReceiptDetailView.as_view(), name='sales_receipt_detail'),
    path('sales/receipt/detail/<int:pk>/pdf', views.print_receipt,name='receiptpdf'),
    path('sales/receipt/update/<int:pk>/', views.ReceiptUpdateView.as_view(), name='sales_receipt_update'),
    path('sales/receipt/delete/<int:pk>/', views.ReceiptDeleteView.as_view(), name='sales_receipt_delete'),
)

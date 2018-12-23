from django.urls import path, include
from rest_framework import routers

from . import api
from . import views

router = routers.DefaultRouter()
router.register(r'invoice', api.InvoiceViewSet)
router.register(r'invoiceitem', api.InvoiceItemViewSet)
router.register(r'payment', api.PaymentViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Invoice
    path('purchase/invoice/', views.InvoiceListView.as_view(), name='purchase_invoice_list'),
    path('purchase/invoice/create/', views.InvoiceCreateView.as_view(), name='purchase_invoice_create'),
    path('purchase/invoice/detail/<slug:slug>/', views.InvoiceDetailView.as_view(), name='purchase_invoice_detail'),
    path('purchase/invoice/update/<slug:slug>/', views.InvoiceUpdateView.as_view(), name='purchase_invoice_update'),
)

urlpatterns += (
    # urls for InvoiceItem
    path('purchase/invoiceitem/', views.InvoiceItemListView.as_view(), name='purchase_invoiceitem_list'),
    path('purchase/invoiceitem/create/', views.InvoiceItemCreateView.as_view(), name='purchase_invoiceitem_create'),
    path('purchase/invoiceitem/detail/<int:pk>/', views.InvoiceItemDetailView.as_view(), name='purchase_invoiceitem_detail'),
    path('purchase/invoiceitem/update/<int:pk>/', views.InvoiceItemUpdateView.as_view(), name='purchase_invoiceitem_update'),
)

urlpatterns += (
    # urls for Payment
    path('purchase/payment/', views.PaymentListView.as_view(), name='purchase_payment_list'),
    path('purchase/payment/create/', views.PaymentCreateView.as_view(), name='purchase_payment_create'),
    path('purchase/payment/detail/<slug:slug>/', views.PaymentDetailView.as_view(), name='purchase_payment_detail'),
    path('purchase/payment/update/<slug:slug>/', views.PaymentUpdateView.as_view(), name='purchase_payment_update'),
)


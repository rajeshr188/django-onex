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
    path('purchase/home/',views.home,name = 'purchase_home'),
    path('purchase/invoice/postall/',views.post_all_purchase,name='purchase_invoice_postall'),
    path('purchase/invlice/unpostall/', views.unpost_all_purchase,
         name='purchase_invoice_unpostall'),

    path('purchase/invoice/', views.InvoiceListView.as_view(), name='purchase_invoice_list'),
    path('purchase/invoice/create/', views.InvoiceCreateView.as_view(), name='purchase_invoice_create'),
    path('purchase/invoice/detail/<int:pk>/', views.InvoiceDetailView.as_view(), name='purchase_invoice_detail'),
    path('purchase/invoice/detail/<int:pk>/pdf', views.print_invoice,name='invoicepdf'),
    path('purchase/invoice/update/<int:pk>/', views.InvoiceUpdateView.as_view(), name='purchase_invoice_update'),
    path('purchase/invoice/delete/<int:pk>/', views.InvoiceDeleteView.as_view(), name='purchase_invoice_delete'),
    path('purchase/invoice/<int:pk>/post/',views.post_purchase,name = 'purchase_invoice_post'),
    path('purchase/invoice/<int:pk>/unpost/',views.unpost_purchase,name='purchase_invoice_unpost'),
)
urlpatterns+=(
            path('purchase/balance/',views.list_balance,name='purchase_balance'),
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
    path('purchase/payment/detail/<int:pk>/', views.PaymentDetailView.as_view(), name='purchase_payment_detail'),
    path('purchase/payment/detail/<int:id>/pdf', views.print_payment,name='paymentpdf'),
    path('purchase/payment/update/<int:pk>/', views.PaymentUpdateView.as_view(), name='purchase_payment_update'),
    path('purchase/payment/delete/<int:pk>/', views.PaymentDeleteView.as_view(), name='purchase_payment_delete'),
    path('purchase/payment/<int:pk>/post/',views.post_payment,name = 'purchase_payment_post'),
    path('purchase/payment/<int:pk>/unpost/',views.unpost_payment,name='purchase_payment_unpost'),
    path('purchase/payment/postall/', views.post_all_payment,
         name='purchase_invoice_postall'),
    path('purchase/payment/unpostall/', views.unpost_all_payment,
         name='purchase_invoice_unpostall'),


)

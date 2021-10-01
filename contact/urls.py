from django.urls import path, include
from rest_framework import routers

from . import api
from . import views

router = routers.DefaultRouter()
router.register(r'customer', api.CustomerViewSet)
# router.register(r'supplier', api.SupplierViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Customer
    path('',views.home,name='contact_home'),
    path('import/',views.simple_upload,name='customer_import'),
    # path('importaccstmt/', views.import_accstmt, name='customer_import_accstmt'),

    path('importpurctxns/',views.import_purctxns,name = 'customer_import_purchase'),
    path('importsalestxns/', views.import_salestxns, name='customer_import_txns_sales'),
    path('importreceipttxns/',views.import_receipttxns,name = 'customer_import_txns_receipt'),
    path('importpaymenttxns/',views.import_paymenttxns,name = 'customer_import_txns_payment'),

    path('customer/', views.CustomerListView.as_view(), name='contact_customer_list'),
    path('customer/create/', views.CustomerCreateView.as_view(), name='contact_customer_create'),
    path('customer/detail/<int:pk>/', views.CustomerDetailView.as_view(), name='contact_customer_detail'),
    path('customer/update/<int:pk>/', views.CustomerUpdateView.as_view(), name='contact_customer_update'),
    path('customer/<int:pk>/delete/',views.CustomerDelete.as_view(),name='contact_customer_delete'),
    path('customer/<int:pk>/reallot_receipts/',views.reallot_receipts, name='contact_reallot_receipts'),
    path('customer/<int:pk>/reallot_payments/', views.reallot_payments,
         name='contact_reallot_payments'),
)


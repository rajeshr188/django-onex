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
    path('customer/', views.CustomerListView.as_view(), name='contact_customer_list'),
    path('customer/create/', views.CustomerCreateView.as_view(), name='contact_customer_create'),
    path('customer/detail/<int:pk>/', views.CustomerDetailView.as_view(), name='contact_customer_detail'),
    path('customer/update/<int:pk>/', views.CustomerUpdateView.as_view(), name='contact_customer_update'),
    path('customer/<int:pk>/delete/',views.CustomerDelete.as_view(),name='contact_customer_delete'),
    path('customer/<int:pk>/reallot/',views.reallot_receipts, name='contact_reallot_receipts')
)

# urlpatterns += (
#     # urls for Supplier
#     path('supplier/', views.SupplierListView.as_view(), name='contact_supplier_list'),
#     path('supplier/create/', views.SupplierCreateView.as_view(), name='contact_supplier_create'),
#     path('supplier/detail/<int:pk>/', views.SupplierDetailView.as_view(), name='contact_supplier_detail'),
#     path('supplier/update/<int:pk>/', views.SupplierUpdateView.as_view(), name='contact_supplier_update'),
#     path('supplier/<int:pk>/delete',views.SupplierDelete.as_view(),name='contact_supplier_delete'),
# )

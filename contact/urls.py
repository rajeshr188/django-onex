from django.urls import path, include
from rest_framework import routers

from . import api
from . import views

router = routers.DefaultRouter()
router.register(r'customer', api.CustomerViewSet)
router.register(r'supplier', api.SupplierViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Customer
    path('',views.home,name='contact_home'),
    path('customer/', views.CustomerListView.as_view(), name='contact_customer_list'),
    path('customer/create/', views.CustomerCreateView.as_view(), name='contact_customer_create'),
    path('customer/detail/<slug:slug>/', views.CustomerDetailView.as_view(), name='contact_customer_detail'),
    path('customer/update/<slug:slug>/', views.CustomerUpdateView.as_view(), name='contact_customer_update'),
    path('customer/<slug:slug>/delete/',views.CustomerDelete.as_view(),name='contact_customer_delete'),
)

urlpatterns += (
    # urls for Supplier
    path('supplier/', views.SupplierListView.as_view(), name='contact_supplier_list'),
    path('supplier/create/', views.SupplierCreateView.as_view(), name='contact_supplier_create'),
    path('supplier/detail/<slug:slug>/', views.SupplierDetailView.as_view(), name='contact_supplier_detail'),
    path('supplier/update/<slug:slug>/', views.SupplierUpdateView.as_view(), name='contact_supplier_update'),
    path('supplier/<int:pk>/delete',views.SupplierDelete.as_view(),name='contact_supplier_delete'),
)

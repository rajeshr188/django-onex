
from django.urls import path, include
from rest_framework import routers

from . import api
from . import views

router = routers.DefaultRouter()
router.register(r'category', api.CategoryViewSet)
router.register(r'producttype', api.ProductTypeViewSet)
router.register(r'product', api.ProductViewSet)
router.register(r'productvariant', api.ProductVariantViewSet)
router.register(r'attribute', api.AttributeViewSet)
router.register(r'attributevalue', api.AttributeValueViewSet)
router.register(r'productimage', api.ProductImageViewSet)
router.register(r'variantimage', api.VariantImageViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Category
    path('category/', views.CategoryListView.as_view(), name='product_category_list'),
    path('category/create/', views.CategoryCreateView.as_view(), name='product_category_create'),
    path('category/detail/<slug:slug>/', views.CategoryDetailView.as_view(), name='product_category_detail'),
    path('category/update/<slug:slug>/', views.CategoryUpdateView.as_view(), name='product_category_update'),
)

urlpatterns += (
    # urls for ProductType
    path('producttype/', views.ProductTypeListView.as_view(), name='product_producttype_list'),
    path('producttype/create/', views.ProductTypeCreateView.as_view(), name='product_producttype_create'),
    path('producttype/detail/<int:pk>/', views.ProductTypeDetailView.as_view(), name='product_producttype_detail'),
    path('producttype/update/<int:pk>/', views.ProductTypeUpdateView.as_view(), name='product_producttype_update'),
)

urlpatterns += (
    # urls for Product
    path('product/', views.ProductListView.as_view(), name='product_product_list'),
    path('product/create/<int:type_pk>/', views.product_create, name='product_product_create'),
    path('product/detail/<int:pk>/', views.ProductDetailView.as_view(), name='product_product_detail'),
    path('product/update/<int:pk>/', views.product_edit, name='product_product_update'),
)

urlpatterns += (
    # urls for ProductVariant
    path('productvariant/', views.ProductVariantListView.as_view(), name='product_productvariant_list'),
    path('productvariant/create/<int:pk>', views.variant_create, name='product_productvariant_create'),
    path('productvariant/detail/<int:pk>/', views.ProductVariantDetailView.as_view(), name='product_productvariant_detail'),
    path('productvariant/update/<int:pk>/', views.ProductVariantUpdateView.as_view(), name='product_productvariant_update'),
)

urlpatterns += (
    # urls for Attribute
    path('attribute/', views.AttributeListView.as_view(), name='product_attribute_list'),
    path('attribute/create/', views.AttributeCreateView.as_view(), name='product_attribute_create'),
    path('attribute/detail/<slug:slug>/', views.AttributeDetailView.as_view(), name='product_attribute_detail'),
    path('attribute/update/<slug:slug>/', views.AttributeUpdateView.as_view(), name='product_attribute_update'),
)

urlpatterns += (
    # urls for AttributeValue
    path('attributevalue/', views.AttributeValueListView.as_view(), name='product_attributevalue_list'),
    path('attributevalue/create/', views.AttributeValueCreateView.as_view(), name='product_attributevalue_create'),
    path('attributevalue/detail/<slug:slug>/', views.AttributeValueDetailView.as_view(), name='product_attributevalue_detail'),
    path('attributevalue/update/<slug:slug>/', views.AttributeValueUpdateView.as_view(), name='product_attributevalue_update'),
)

urlpatterns += (
    # urls for ProductImage
    path('productimage/', views.ProductImageListView.as_view(), name='product_productimage_list'),
    path('productimage/create/', views.ProductImageCreateView.as_view(), name='product_productimage_create'),
    path('productimage/detail/<int:pk>/', views.ProductImageDetailView.as_view(), name='product_productimage_detail'),
    path('productimage/update/<int:pk>/', views.ProductImageUpdateView.as_view(), name='product_productimage_update'),
)

urlpatterns += (
    # urls for VariantImage
    path('variantimage/', views.VariantImageListView.as_view(), name='product_variantimage_list'),
    path('variantimage/create/', views.VariantImageCreateView.as_view(), name='product_variantimage_create'),
    path('variantimage/detail/<int:pk>/', views.VariantImageDetailView.as_view(), name='product_variantimage_detail'),
    path('variantimage/update/<int:pk>/', views.VariantImageUpdateView.as_view(), name='product_variantimage_update'),
)
urlpatterns +=(
    #urls for Stock
    path('stock/',views.StockListView.as_view(),name='product_stock_list'),
    path('stock/create/',views.StockCreateView.as_view(),name='product_stock_create'),
    path('stock/detail/<slug:slug>/',views.StockDetailView.as_view(),name='product_stock_detail'),
    path('stock/update/<int:pk>/',views.StockUpdateView.as_view(),name='product_stock_update'),
)
urlpatterns +=(
    #urls for Stocktransaction
    path('stocktransaction/',views.StockTransactionListView.as_view(),name='product_stocktransaction_list'),
    path('stocktransaction/create/',views.StockTransactionCreateView.as_view(),name='product_stocktransaction_create'),
    path('stocktransaction/detail/<int:pk>/',views.StockTransactionDetailView.as_view(),name='product_stocktransaction_detail'),
    path('stocktransaction/update/<int:pk>/',views.StockTransactionUpdateView.as_view(),name='product_stocktransaction_update'),
)

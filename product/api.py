from . import models
from . import serializers
from rest_framework import viewsets, permissions


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for the Category class"""

    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for the ProductType class"""

    queryset = models.ProductType.objects.all()
    serializer_class = serializers.ProductTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for the Product class"""

    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductVariantViewSet(viewsets.ModelViewSet):
    """ViewSet for the ProductVariant class"""

    queryset = models.ProductVariant.objects.all()
    serializer_class = serializers.ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttributeViewSet(viewsets.ModelViewSet):
    """ViewSet for the Attribute class"""

    queryset = models.Attribute.objects.all()
    serializer_class = serializers.AttributeSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttributeValueViewSet(viewsets.ModelViewSet):
    """ViewSet for the AttributeValue class"""

    queryset = models.AttributeValue.objects.all()
    serializer_class = serializers.AttributeValueSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductImageViewSet(viewsets.ModelViewSet):
    """ViewSet for the ProductImage class"""

    queryset = models.ProductImage.objects.all()
    serializer_class = serializers.ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated]


class VariantImageViewSet(viewsets.ModelViewSet):
    """ViewSet for the VariantImage class"""

    queryset = models.VariantImage.objects.all()
    serializer_class = serializers.VariantImageSerializer
    permission_classes = [permissions.IsAuthenticated]

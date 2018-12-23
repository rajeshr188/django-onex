from . import models

from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Category
        fields = (
            'slug',
            'name',
            'description',
        )


class ProductTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ProductType
        fields = (
            'pk',
            'name',
            'has_variants',
        )


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Product
        fields = (
            'pk',
            'name',
            'description',
            
        )


class ProductVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ProductVariant
        fields = (
            'pk',
            'sku',
            'name',
            'track_inventory',
            'quantity',
            'cost_price',
            'weight',
        )


class AttributeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Attribute
        fields = (
            'slug',
            'name',
        )


class AttributeValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AttributeValue
        fields = (
            'slug',
            'name',
            'value',
        )


class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ProductImage
        fields = (
            'pk',
            'ppoi',
            'alt',
        )


class VariantImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.VariantImage
        fields = (
            'pk',
        )

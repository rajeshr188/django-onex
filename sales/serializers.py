from . import models

from rest_framework import serializers


class InvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Invoice
        fields = (
            'slug', 
            'created', 
            'last_updated', 
            'rate', 
            'balancetype', 
            'paymenttype', 
            'balance', 
            'status', 
        )


class InvoiceItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.InvoiceItem
        fields = (
            'pk', 
            'weight', 
            'touch', 
            'total', 
            'is_return', 
            'quantity', 
        )


class ReceiptSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Receipt
        fields = (
            'slug', 
            'created', 
            'last_updated', 
            'type', 
            'total', 
            'description', 
        )



from . import models
from . import serializers
from rest_framework import viewsets, permissions


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for the Invoice class"""

    queryset = models.Invoice.objects.all()
    serializer_class = serializers.InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """ViewSet for the InvoiceItem class"""

    queryset = models.InvoiceItem.objects.all()
    serializer_class = serializers.InvoiceItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for the Payment class"""

    queryset = models.Payment.objects.all()
    serializer_class = serializers.PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]



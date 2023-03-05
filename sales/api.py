from rest_framework import permissions, viewsets

from . import models, serializers


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


class ReceiptViewSet(viewsets.ModelViewSet):
    """ViewSet for the Receipt class"""

    queryset = models.Receipt.objects.all()
    serializer_class = serializers.ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated]

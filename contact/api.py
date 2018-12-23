from . import models
from . import serializers
from rest_framework import viewsets, permissions


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for the Customer class"""

    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for the Supplier class"""

    queryset = models.Supplier.objects.all()
    serializer_class = serializers.SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]



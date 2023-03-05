from rest_framework import permissions, viewsets

from . import models, serializers
from .filters import CustomerFilter


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for the Customer class"""

    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    filterset_class = CustomerFilter
    search_fields = ["name", "relatedas", "relatedto"]
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]

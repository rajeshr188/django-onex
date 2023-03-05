from rest_framework import permissions, viewsets

from . import models, serializers


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for the Contact class"""

    queryset = models.Contact.objects.all()
    serializer_class = serializers.ContactSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChitViewSet(viewsets.ModelViewSet):
    """ViewSet for the Chit class"""

    queryset = models.Chit.objects.all()
    serializer_class = serializers.ChitSerializer
    permission_classes = [permissions.IsAuthenticated]


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Collection class"""

    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]


class AllotmentViewSet(viewsets.ModelViewSet):
    """ViewSet for the Allotment class"""

    queryset = models.Allotment.objects.all()
    serializer_class = serializers.AllotmentSerializer
    permission_classes = [permissions.IsAuthenticated]

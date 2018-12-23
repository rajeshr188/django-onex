from . import models
from . import serializers
from rest_framework import viewsets, permissions


class LicenseViewSet(viewsets.ModelViewSet):
    """ViewSet for the License class"""

    queryset = models.License.objects.all()
    serializer_class = serializers.LicenseSerializer
    permission_classes = [permissions.IsAuthenticated]


class LoanViewSet(viewsets.ModelViewSet):
    """ViewSet for the Loan class"""

    queryset = models.Loan.objects.all()
    serializer_class = serializers.LoanSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReleaseViewSet(viewsets.ModelViewSet):
    """ViewSet for the Release class"""

    queryset = models.Release.objects.all()
    serializer_class = serializers.ReleaseSerializer
    permission_classes = [permissions.IsAuthenticated]



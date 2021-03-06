from . import models
from rest_framework import serializers


class LicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.License
        fields = (
            'id',
            'name',
            'created',
            'last_updated',
            'type',
            'shopname',
            'address',
            'phonenumber',
            'propreitor',
        )


class LoanSerializer(serializers.ModelSerializer):
    # customer = serializers.StringRelatedField()
    class Meta:
        model = models.Loan
        fields = (
            'id',
            'loanid',
            'customer',
            'created',
            'license',
            'last_updated',
            'itemtype',
            'itemdesc',
            'itemweight',
            'itemvalue',
            'loanamount',
            'interestrate',
            'interest',
        )


class ReleaseSerializer(serializers.ModelSerializer):
    # loan = serializers.StringRelatedField()
    class Meta:
        model = models.Release
        fields = (
            'id',
            'releaseid',
            'loan',
            # 'customer',
            'created',
            'last_updated',
            'interestpaid',
        )

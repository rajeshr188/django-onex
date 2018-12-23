from . import models

from rest_framework import serializers


class LicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.License
        fields = (
            'slug',
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

    class Meta:
        model = models.Loan
        fields = (
            'slug',
            'loanid',
            'customer',
            'created',
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

    class Meta:
        model = models.Release
        fields = (
            'slug',
            'releaseid',
            'loan',
            'customer',
            'created',
            'last_updated',
            'interestpaid',
        )

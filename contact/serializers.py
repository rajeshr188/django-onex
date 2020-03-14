from . import models

from rest_framework import serializers


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Customer
        fields = (
            'id',
            'name',
            'created',
            'last_updated',
            'phonenumber',
            'Address',
            'type',
            'relatedas',
            'relatedto',
        )


# class SupplierSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = models.Supplier
#         fields = (
#             'id',
#             'name',
#             'created',
#             'last_updated',
#             'organisation',
#             'phonenumber',
#             'initial',
#         )

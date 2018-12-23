from . import models

from rest_framework import serializers


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Contact
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'phoneno', 
        )


class ChitSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Chit
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'type', 
            'amount', 
            'commission', 
            'member_limit', 
            'date_to_allot', 
        )


class CollectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Collection
        fields = (
            'slug', 
            'date_collected', 
            'amount', 
        )


class AllotmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Allotment
        fields = (
            'slug', 
            'amount', 
            'created', 
        )



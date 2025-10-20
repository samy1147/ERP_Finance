from rest_framework import serializers
from ar.models import Customer
from ap.models import Supplier


class CustomerSerializer(serializers.ModelSerializer):
    currency_name = serializers.CharField(source='currency.code', read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'code', 'name', 'email', 'country', 'currency', 'currency_name', 
                  'vat_number', 'is_active']
        read_only_fields = ['id']


class SupplierSerializer(serializers.ModelSerializer):
    currency_name = serializers.CharField(source='currency.code', read_only=True)
    
    class Meta:
        model = Supplier
        fields = ['id', 'code', 'name', 'email', 'country', 'currency', 'currency_name', 
                  'vat_number', 'is_active']
        read_only_fields = ['id']

"""
Test the API response includes can_delete and deletion_blockers
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from ap.models import Supplier
from ap.serializers import SupplierDetailSerializer, SupplierListSerializer

# Get supplier #7
supplier = Supplier.objects.get(id=7)

# Test detail serializer
detail_serializer = SupplierDetailSerializer(supplier)
data = detail_serializer.data

print("Detail Serializer:")
print(f"  can_delete: {data.get('can_delete')}")
print(f"  deletion_blockers: {data.get('deletion_blockers')}")

# Test list serializer
list_serializer = SupplierListSerializer(supplier)
list_data = list_serializer.data

print("\nList Serializer:")
print(f"  can_delete: {list_data.get('can_delete')}")
print(f"  deletion_blockers: {list_data.get('deletion_blockers')}")

# Test with deletable supplier
suppliers_can_delete = Supplier.objects.filter(apinvoice__isnull=True)[:1]
if suppliers_can_delete:
    test_supplier = suppliers_can_delete[0]
    test_data = SupplierDetailSerializer(test_supplier).data
    print(f"\nDeletable Supplier ({test_supplier.code}):")
    print(f"  can_delete: {test_data.get('can_delete')}")
    print(f"  deletion_blockers: {test_data.get('deletion_blockers')}")

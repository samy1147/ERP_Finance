"""
Test the can_delete functionality for Supplier model
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from ap.models import Supplier

# Get supplier #7
supplier = Supplier.objects.get(id=7)

print(f"Supplier: {supplier}")
print(f"Can delete: {supplier.can_delete}")
print(f"Deletion blockers: {supplier.get_deletion_blockers()}")

# Test with a supplier that can be deleted (if any)
suppliers_can_delete = Supplier.objects.filter(
    apinvoice__isnull=True
)[:1]

if suppliers_can_delete:
    test_supplier = suppliers_can_delete[0]
    print(f"\nTest Supplier: {test_supplier}")
    print(f"Can delete: {test_supplier.can_delete}")
    print(f"Deletion blockers: {test_supplier.get_deletion_blockers()}")

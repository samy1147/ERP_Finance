"""
Test script to verify invoice totals are stored in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from ar.models import ARInvoice
from ap.models import APInvoice
from finance.serializers import ARInvoiceSerializer, APInvoiceSerializer

print("=" * 60)
print("Testing Invoice Totals Storage")
print("=" * 60)

# Test AR Invoice
print("\n--- AR Invoice Test ---")
ar_inv = ARInvoice.objects.first()
if ar_inv:
    print(f"Invoice Number: {ar_inv.number}")
    print(f"Database Fields:")
    print(f"  - subtotal: {ar_inv.subtotal}")
    print(f"  - tax_amount: {ar_inv.tax_amount}")
    print(f"  - total: {ar_inv.total}")
    
    # Test serializer output
    serializer = ARInvoiceSerializer(ar_inv)
    data = serializer.data
    print(f"\nAPI Response Fields:")
    print(f"  - subtotal: {data.get('subtotal')}")
    print(f"  - tax_amount: {data.get('tax_amount')}")
    print(f"  - total: {data.get('total')}")
    
    # Test calculate method
    print(f"\nRecalculating totals...")
    ar_inv.calculate_and_save_totals()
    print(f"After recalculation:")
    print(f"  - subtotal: {ar_inv.subtotal}")
    print(f"  - tax_amount: {ar_inv.tax_amount}")
    print(f"  - total: {ar_inv.total}")
else:
    print("No AR invoices found in database")

# Test AP Invoice
print("\n--- AP Invoice Test ---")
ap_inv = APInvoice.objects.first()
if ap_inv:
    print(f"Invoice Number: {ap_inv.number}")
    print(f"Database Fields:")
    print(f"  - subtotal: {ap_inv.subtotal}")
    print(f"  - tax_amount: {ap_inv.tax_amount}")
    print(f"  - total: {ap_inv.total}")
    
    # Test serializer output
    serializer = APInvoiceSerializer(ap_inv)
    data = serializer.data
    print(f"\nAPI Response Fields:")
    print(f"  - subtotal: {data.get('subtotal')}")
    print(f"  - tax_amount: {data.get('tax_amount')}")
    print(f"  - total: {data.get('total')}")
    
    # Test calculate method
    print(f"\nRecalculating totals...")
    ap_inv.calculate_and_save_totals()
    print(f"After recalculation:")
    print(f"  - subtotal: {ap_inv.subtotal}")
    print(f"  - tax_amount: {ap_inv.tax_amount}")
    print(f"  - total: {ap_inv.total}")
else:
    print("No AP invoices found in database")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)

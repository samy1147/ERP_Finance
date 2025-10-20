"""
Test script to verify payment allocation currency tracking
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from decimal import Decimal
from ar.models import ARPaymentAllocation
from ap.models import APPaymentAllocation

print("=" * 70)
print("Payment Allocation Currency Tracking Test")
print("=" * 70)

# Test AR Payment Allocations
print("\n--- AR Payment Allocations ---")
ar_allocations = ARPaymentAllocation.objects.all()

if ar_allocations.exists():
    for alloc in ar_allocations:
        print(f"\nAllocation #{alloc.id}:")
        print(f"  Payment: {alloc.payment.reference}")
        print(f"  Invoice: {alloc.invoice.number}")
        print(f"  Amount: {alloc.amount}")
        print(f"  Invoice Currency: {alloc.invoice_currency.code if alloc.invoice_currency else 'Not set'}")
        print(f"  Exchange Rate: {alloc.current_exchange_rate if alloc.current_exchange_rate else 'Not set'}")
        
        # Show the currencies involved
        if alloc.payment.currency and alloc.invoice.currency:
            print(f"  Payment Currency: {alloc.payment.currency.code}")
            print(f"  Invoice Currency: {alloc.invoice.currency.code}")
            
            if alloc.payment.currency.id != alloc.invoice.currency.id:
                print(f"  ⚠️  Cross-currency payment detected!")
                if alloc.current_exchange_rate:
                    print(f"  Exchange Rate: 1 {alloc.invoice.currency.code} = {alloc.current_exchange_rate} {alloc.payment.currency.code}")
            else:
                print(f"  ✅ Same currency payment")
else:
    print("No AR payment allocations found")

# Test AP Payment Allocations
print("\n--- AP Payment Allocations ---")
ap_allocations = APPaymentAllocation.objects.all()

if ap_allocations.exists():
    for alloc in ap_allocations:
        print(f"\nAllocation #{alloc.id}:")
        print(f"  Payment: {alloc.payment.reference}")
        print(f"  Invoice: {alloc.invoice.number}")
        print(f"  Amount: {alloc.amount}")
        print(f"  Invoice Currency: {alloc.invoice_currency.code if alloc.invoice_currency else 'Not set'}")
        print(f"  Exchange Rate: {alloc.current_exchange_rate if alloc.current_exchange_rate else 'Not set'}")
        
        # Show the currencies involved
        if alloc.payment.currency and alloc.invoice.currency:
            print(f"  Payment Currency: {alloc.payment.currency.code}")
            print(f"  Invoice Currency: {alloc.invoice.currency.code}")
            
            if alloc.payment.currency.id != alloc.invoice.currency.id:
                print(f"  ⚠️  Cross-currency payment detected!")
                if alloc.current_exchange_rate:
                    print(f"  Exchange Rate: 1 {alloc.invoice.currency.code} = {alloc.current_exchange_rate} {alloc.payment.currency.code}")
            else:
                print(f"  ✅ Same currency payment")
else:
    print("No AP payment allocations found")

# Test auto-population by re-saving existing allocations
print("\n" + "=" * 70)
print("Testing Auto-Population of Currency Fields")
print("=" * 70)

for alloc in ARPaymentAllocation.objects.all():
    print(f"\nRe-saving AR Allocation #{alloc.id}...")
    alloc.save()
    alloc.refresh_from_db()
    print(f"  Invoice Currency: {alloc.invoice_currency.code if alloc.invoice_currency else 'NULL'}")
    print(f"  Exchange Rate: {alloc.current_exchange_rate if alloc.current_exchange_rate else 'NULL'}")

for alloc in APPaymentAllocation.objects.all():
    print(f"\nRe-saving AP Allocation #{alloc.id}...")
    alloc.save()
    alloc.refresh_from_db()
    print(f"  Invoice Currency: {alloc.invoice_currency.code if alloc.invoice_currency else 'NULL'}")
    print(f"  Exchange Rate: {alloc.current_exchange_rate if alloc.current_exchange_rate else 'NULL'}")

print("\n" + "=" * 70)
print("✅ Test Complete!")
print("=" * 70)

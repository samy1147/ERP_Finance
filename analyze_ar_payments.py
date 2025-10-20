"""
Analyze AR Payment records to see field usage
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from ar.models import ARPayment

print("AR Payment Records Analysis:")
print("=" * 70)

payments = ARPayment.objects.all()[:10]

if not payments:
    print("No payment records found.")
else:
    for p in payments:
        print(f"Payment #{p.id}:")
        print(f"  - amount (deprecated):     {p.amount}")
        print(f"  - total_amount (current):  {p.total_amount}")
        print(f"  - invoice (old system):    {p.invoice}")
        print(f"  - customer (new system):   {p.customer}")
        print(f"  - allocations count:       {p.allocations.count()}")
        
        if p.allocations.exists():
            print(f"  - allocation details:")
            for alloc in p.allocations.all():
                print(f"      → Invoice {alloc.invoice.number}: {alloc.amount}")
        
        print("-" * 70)

print("\nSummary:")
print(f"Total payments: {ARPayment.objects.count()}")
print(f"Using old 'amount' field: {ARPayment.objects.filter(amount__isnull=False).count()}")
print(f"Using new 'total_amount' field: {ARPayment.objects.filter(total_amount__isnull=False).count()}")
print(f"With allocations: {ARPayment.objects.filter(allocations__isnull=False).distinct().count()}")

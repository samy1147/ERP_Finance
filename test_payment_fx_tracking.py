"""
Test FX Gain/Loss Tracking in Payments
Demonstrates how invoice_currency and exchange_rate are stored in payment table
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from decimal import Decimal
from ar.models import ARPayment, ARPaymentAllocation
from ap.models import APPayment, APPaymentAllocation

print("=" * 80)
print("PAYMENT FX TRACKING TEST")
print("=" * 80)

# Test AR Payments
print("\n" + "=" * 80)
print("AR PAYMENTS - FX Tracking")
print("=" * 80)

for payment in ARPayment.objects.all():
    print(f"\n{'─' * 80}")
    print(f"Payment Reference: {payment.reference}")
    print(f"Payment Date: {payment.date}")
    print(f"Payment Amount: {payment.total_amount} {payment.currency.code if payment.currency else 'N/A'}")
    
    # Show current FX fields
    print(f"\n📊 FX Tracking (BEFORE update):")
    print(f"  Invoice Currency: {payment.invoice_currency.code if payment.invoice_currency else 'NOT SET'}")
    print(f"  Exchange Rate: {payment.exchange_rate if payment.exchange_rate else 'NOT SET'}")
    
    # Show allocations
    print(f"\n💰 Payment Allocations:")
    for alloc in payment.allocations.all():
        print(f"  → Invoice {alloc.invoice.number}")
        print(f"     Amount: {alloc.amount}")
        print(f"     Invoice Currency: {alloc.invoice.currency.code}")
        print(f"     Payment Currency: {payment.currency.code if payment.currency else 'N/A'}")
        
        if alloc.invoice.currency.id != payment.currency.id:
            print(f"     🔄 CROSS-CURRENCY PAYMENT DETECTED")
    
    # Update exchange rate from allocations
    print(f"\n🔄 Updating exchange rate from allocations...")
    payment.update_exchange_rate_from_allocations()
    payment.refresh_from_db()
    
    # Show updated FX fields
    print(f"\n📊 FX Tracking (AFTER update):")
    print(f"  Invoice Currency: {payment.invoice_currency.code if payment.invoice_currency else 'NOT SET'}")
    print(f"  Exchange Rate: {payment.exchange_rate if payment.exchange_rate else 'NOT SET'}")
    
    # Calculate FX impact
    if payment.exchange_rate and payment.invoice_currency and payment.currency:
        if payment.invoice_currency.id != payment.currency.id:
            print(f"\n💱 Exchange Rate Details:")
            print(f"  Rate: 1 {payment.invoice_currency.code} = {payment.exchange_rate} {payment.currency.code}")
            print(f"  This rate will be used for FX gain/loss calculations")

# Test AP Payments
print("\n" + "=" * 80)
print("AP PAYMENTS - FX Tracking")
print("=" * 80)

for payment in APPayment.objects.all():
    print(f"\n{'─' * 80}")
    print(f"Payment Reference: {payment.reference}")
    print(f"Payment Date: {payment.date}")
    print(f"Payment Amount: {payment.total_amount} {payment.currency.code if payment.currency else 'N/A'}")
    
    # Show current FX fields
    print(f"\n📊 FX Tracking (BEFORE update):")
    print(f"  Invoice Currency: {payment.invoice_currency.code if payment.invoice_currency else 'NOT SET'}")
    print(f"  Exchange Rate: {payment.exchange_rate if payment.exchange_rate else 'NOT SET'}")
    
    # Show allocations
    print(f"\n💰 Payment Allocations:")
    for alloc in payment.allocations.all():
        print(f"  → Invoice {alloc.invoice.number}")
        print(f"     Amount: {alloc.amount}")
        print(f"     Invoice Currency: {alloc.invoice.currency.code}")
        print(f"     Payment Currency: {payment.currency.code if payment.currency else 'N/A'}")
        
        if alloc.invoice.currency.id != payment.currency.id:
            print(f"     🔄 CROSS-CURRENCY PAYMENT DETECTED")
    
    # Update exchange rate from allocations
    print(f"\n🔄 Updating exchange rate from allocations...")
    payment.update_exchange_rate_from_allocations()
    payment.refresh_from_db()
    
    # Show updated FX fields
    print(f"\n📊 FX Tracking (AFTER update):")
    print(f"  Invoice Currency: {payment.invoice_currency.code if payment.invoice_currency else 'NOT SET'}")
    print(f"  Exchange Rate: {payment.exchange_rate if payment.exchange_rate else 'NOT SET'}")
    
    # Calculate FX impact
    if payment.exchange_rate and payment.invoice_currency and payment.currency:
        if payment.invoice_currency.id != payment.currency.id:
            print(f"\n💱 Exchange Rate Details:")
            print(f"  Rate: 1 {payment.invoice_currency.code} = {payment.exchange_rate} {payment.currency.code}")
            print(f"  This rate will be used for FX gain/loss calculations")

print("\n" + "=" * 80)
print("FX GAIN/LOSS CALCULATION EXAMPLE")
print("=" * 80)

for payment in ARPayment.objects.all():
    if payment.exchange_rate and payment.invoice_currency and payment.currency:
        if payment.invoice_currency.id != payment.currency.id:
            print(f"\nPayment: {payment.reference}")
            print(f"─" * 40)
            
            for alloc in payment.allocations.all():
                invoice = alloc.invoice
                
                # Invoice posted at one rate
                invoice_rate = invoice.exchange_rate or Decimal('0')
                # Payment made at current rate
                payment_rate = payment.exchange_rate or Decimal('0')
                
                if invoice_rate and payment_rate:
                    print(f"\nInvoice {invoice.number}:")
                    print(f"  Invoice posted rate: {invoice_rate}")
                    print(f"  Payment made at rate: {payment_rate}")
                    
                    # Calculate difference
                    rate_diff = payment_rate - invoice_rate
                    amount_in_invoice_currency = alloc.amount / payment_rate if payment_rate else Decimal('0')
                    fx_impact = amount_in_invoice_currency * rate_diff
                    
                    if rate_diff > 0:
                        print(f"  📈 POTENTIAL FX GAIN: {abs(fx_impact):.2f} {payment.currency.code}")
                    elif rate_diff < 0:
                        print(f"  📉 POTENTIAL FX LOSS: {abs(fx_impact):.2f} {payment.currency.code}")
                    else:
                        print(f"  ➡️  No FX gain/loss (rates are equal)")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE!")
print("=" * 80)
print("\nSummary:")
print("- invoice_currency field: Stores the currency of invoices being paid")
print("- exchange_rate field: Stores rate from invoice currency to payment currency")
print("- These fields enable FX gain/loss calculations when payment rate differs from invoice rate")

"""
Script to post existing payments to GL that haven't been posted yet.
This fixes Problem #4: Payments without GL entries.
"""
import django
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from ar.models import ARPayment
from ap.models import APPayment
from decimal import Decimal

def post_ar_payments():
    """Post all AR payments that don't have GL journals"""
    payments_without_gl = ARPayment.objects.filter(gl_journal__isnull=True)
    count = payments_without_gl.count()
    
    print(f"\n{'='*60}")
    print(f"AR PAYMENTS TO POST: {count}")
    print(f"{'='*60}")
    
    if count == 0:
        print("✅ All AR payments already have GL journals!")
        return 0
    
    success_count = 0
    error_count = 0
    
    for payment in payments_without_gl:
        try:
            print(f"\nPosting AR Payment: {payment.reference or f'#{payment.id}'}")
            print(f"  Date: {payment.date}")
            print(f"  Amount: {payment.total_amount or payment.amount}")
            print(f"  Currency: {payment.currency.code if payment.currency else 'N/A'}")
            
            # Post to GL
            je, created, invoices_closed = payment.post_to_gl()
            
            if created:
                print(f"  ✅ Created JournalEntry #{je.id}")
                print(f"     Lines: {je.lines.count()}")
                for line in je.lines.all():
                    print(f"       {line.account.name}: DR {line.debit} CR {line.credit}")
                if invoices_closed:
                    print(f"     Closed invoices: {', '.join(invoices_closed)}")
                success_count += 1
            else:
                print(f"  ⚠️ Already had JournalEntry #{je.id}")
        
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"AR PAYMENTS SUMMARY:")
    print(f"  ✅ Successfully posted: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"{'='*60}")
    
    return success_count

def post_ap_payments():
    """Post all AP payments that don't have GL journals"""
    payments_without_gl = APPayment.objects.filter(gl_journal__isnull=True)
    count = payments_without_gl.count()
    
    print(f"\n{'='*60}")
    print(f"AP PAYMENTS TO POST: {count}")
    print(f"{'='*60}")
    
    if count == 0:
        print("✅ All AP payments already have GL journals!")
        return 0
    
    success_count = 0
    error_count = 0
    
    for payment in payments_without_gl:
        try:
            print(f"\nPosting AP Payment: {payment.reference or f'#{payment.id}'}")
            print(f"  Date: {payment.date}")
            print(f"  Amount: {payment.total_amount or payment.amount}")
            print(f"  Currency: {payment.currency.code if payment.currency else 'N/A'}")
            
            # Post to GL
            je, created, invoices_closed = payment.post_to_gl()
            
            if created:
                print(f"  ✅ Created JournalEntry #{je.id}")
                print(f"     Lines: {je.lines.count()}")
                for line in je.lines.all():
                    print(f"       {line.account.name}: DR {line.debit} CR {line.credit}")
                if invoices_closed:
                    print(f"     Closed invoices: {', '.join(invoices_closed)}")
                success_count += 1
            else:
                print(f"  ⚠️ Already had JournalEntry #{je.id}")
        
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"AP PAYMENTS SUMMARY:")
    print(f"  ✅ Successfully posted: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"{'='*60}")
    
    return success_count

def main():
    print("\n" + "="*60)
    print("PAYMENT GL POSTING SCRIPT")
    print("Fixing Problem #4: GL Posting Logic Not Complete")
    print("="*60)
    
    # Check current status
    ar_total = ARPayment.objects.count()
    ar_with_gl = ARPayment.objects.filter(gl_journal__isnull=False).count()
    ap_total = APPayment.objects.count()
    ap_with_gl = APPayment.objects.filter(gl_journal__isnull=False).count()
    
    print(f"\nCURRENT STATUS:")
    print(f"  AR Payments: {ar_total} total, {ar_with_gl} with GL ({ar_total - ar_with_gl} missing)")
    print(f"  AP Payments: {ap_total} total, {ap_with_gl} with GL ({ap_total - ap_with_gl} missing)")
    
    # Post payments
    ar_posted = post_ar_payments()
    ap_posted = post_ap_payments()
    
    # Final status
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS:")
    print(f"  AR Payments Posted: {ar_posted}")
    print(f"  AP Payments Posted: {ap_posted}")
    print(f"  Total Posted: {ar_posted + ap_posted}")
    print(f"{'='*60}\n")
    
    # Verify
    ar_with_gl_after = ARPayment.objects.filter(gl_journal__isnull=False).count()
    ap_with_gl_after = APPayment.objects.filter(gl_journal__isnull=False).count()
    
    print(f"VERIFICATION:")
    print(f"  AR Payments with GL: {ar_with_gl_after}/{ar_total} ({ar_with_gl_after*100//ar_total if ar_total > 0 else 0}%)")
    print(f"  AP Payments with GL: {ap_with_gl_after}/{ap_total} ({ap_with_gl_after*100//ap_total if ap_total > 0 else 0}%)")
    
    if ar_with_gl_after == ar_total and ap_with_gl_after == ap_total:
        print(f"\n✅ SUCCESS! All payments now have GL journals!")
    else:
        print(f"\n⚠️ Some payments still missing GL journals. Check errors above.")

if __name__ == '__main__':
    main()

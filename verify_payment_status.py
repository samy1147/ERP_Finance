"""Verify payment GL journal posting status"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from ar.models import ARPayment
from ap.models import APPayment

print('\n' + '='*60)
print('AR PAYMENTS STATUS')
print('='*60)
ar_payments = ARPayment.objects.all().order_by('id')
for p in ar_payments:
    ref = p.reference or f'#{p.id}'
    status = f"✅ JE #{p.gl_journal_id}" if p.gl_journal_id else "❌ No GL"
    print(f'{ref:20} | {status:15} | Amount: {p.total_amount or "N/A"}')

ar_total = ar_payments.count()
ar_with_gl = ar_payments.filter(gl_journal__isnull=False).count()
print(f'\nTotal: {ar_total}, With GL: {ar_with_gl}, Missing: {ar_total - ar_with_gl}')

print('\n' + '='*60)
print('AP PAYMENTS STATUS')
print('='*60)
ap_payments = APPayment.objects.all().order_by('id')
for p in ap_payments:
    ref = p.reference or f'#{p.id}'
    status = f"✅ JE #{p.gl_journal_id}" if p.gl_journal_id else "❌ No GL"
    print(f'{ref:20} | {status:15} | Amount: {p.total_amount or "N/A"}')

ap_total = ap_payments.count()
ap_with_gl = ap_payments.filter(gl_journal__isnull=False).count()
print(f'\nTotal: {ap_total}, With GL: {ap_with_gl}, Missing: {ap_total - ap_with_gl}')

print('\n' + '='*60)
print(f'OVERALL: {ar_with_gl + ap_with_gl}/{ar_total + ap_total} payments have GL journals')
print('='*60 + '\n')

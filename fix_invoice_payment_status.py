"""
Direct database script to update AR/AP invoice payment status
"""
import sqlite3
from decimal import Decimal
from datetime import datetime

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("UPDATING INVOICE PAYMENT STATUS")
print("=" * 70)

# Function to calculate invoice total
def calculate_invoice_total(cursor, invoice_id, table_prefix):
    cursor.execute(f'''
        SELECT quantity, unit_price, tax_rate_id
        FROM {table_prefix}_aritem
        WHERE invoice_id = ?
    ''' if table_prefix == 'ar' else f'''
        SELECT quantity, unit_price, tax_rate_id
        FROM {table_prefix}_apitem
        WHERE invoice_id = ?
    ''', (invoice_id,))
    
    items = cursor.fetchall()
    total = Decimal('0.00')
    
    for item in items:
        qty, price, tax_id = item
        subtotal = Decimal(str(qty)) * Decimal(str(price))
        
        if tax_id:
            cursor.execute('SELECT rate FROM core_taxrate WHERE id = ?', (tax_id,))
            tax_rate = cursor.fetchone()
            if tax_rate:
                tax_amount = subtotal * (Decimal(str(tax_rate[0])) / 100)
                subtotal += tax_amount
        
        total += subtotal
    
    return total

# Update AR Invoices
print("\n=== UPDATING AR INVOICES ===\n")

cursor.execute('SELECT id, number, payment_status FROM ar_arinvoice')
ar_invoices = cursor.fetchall()

ar_updated = 0

for invoice in ar_invoices:
    inv_id, inv_number, old_status = invoice
    
    # Calculate total
    total = calculate_invoice_total(cursor, inv_id, 'ar')
    
    # Calculate paid amount
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM ar_arpaymentallocation
        WHERE invoice_id = ?
    ''', (inv_id,))
    paid = Decimal(str(cursor.fetchone()[0]))
    
    outstanding = total - paid
    
    # Determine new status
    if outstanding <= Decimal('0.00'):
        new_status = 'PAID'
        paid_at = datetime.now().isoformat()
    elif paid > Decimal('0.00'):
        new_status = 'PARTIALLY_PAID'
        paid_at = None
    else:
        new_status = 'UNPAID'
        paid_at = None
    
    # Update if changed
    if old_status != new_status:
        if paid_at:
            cursor.execute('''
                UPDATE ar_arinvoice
                SET payment_status = ?, paid_at = ?
                WHERE id = ?
            ''', (new_status, paid_at, inv_id))
        else:
            cursor.execute('''
                UPDATE ar_arinvoice
                SET payment_status = ?, paid_at = NULL
                WHERE id = ?
            ''', (new_status, inv_id))
        
        ar_updated += 1
        print(f"✓ Invoice #{inv_number}: {old_status} → {new_status}")
        print(f"  Total: ${total}, Paid: ${paid}, Outstanding: ${outstanding}\n")

# Update AP Invoices
print("\n=== UPDATING AP INVOICES ===\n")

cursor.execute('SELECT id, number, payment_status FROM ap_apinvoice')
ap_invoices = cursor.fetchall()

ap_updated = 0

for invoice in ap_invoices:
    inv_id, inv_number, old_status = invoice
    
    # Calculate total
    total = calculate_invoice_total(cursor, inv_id, 'ap')
    
    # Calculate paid amount
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM ap_appaymentallocation
        WHERE invoice_id = ?
    ''', (inv_id,))
    paid = Decimal(str(cursor.fetchone()[0]))
    
    outstanding = total - paid
    
    # Determine new status
    if outstanding <= Decimal('0.00'):
        new_status = 'PAID'
        paid_at = datetime.now().isoformat()
    elif paid > Decimal('0.00'):
        new_status = 'PARTIALLY_PAID'
        paid_at = None
    else:
        new_status = 'UNPAID'
        paid_at = None
    
    # Update if changed
    if old_status != new_status:
        if paid_at:
            cursor.execute('''
                UPDATE ap_apinvoice
                SET payment_status = ?, paid_at = ?
                WHERE id = ?
            ''', (new_status, paid_at, inv_id))
        else:
            cursor.execute('''
                UPDATE ap_apinvoice
                SET payment_status = ?, paid_at = NULL
                WHERE id = ?
            ''', (new_status, inv_id))
        
        ap_updated += 1
        print(f"✓ Invoice #{inv_number}: {old_status} → {new_status}")
        print(f"  Total: ${total}, Paid: ${paid}, Outstanding: ${outstanding}\n")

# Commit changes
conn.commit()
conn.close()

print("=" * 70)
print(f"✓ COMPLETE: Updated {ar_updated} AR and {ap_updated} AP invoice(s)")
print("=" * 70)

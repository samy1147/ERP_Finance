import sqlite3
from decimal import Decimal

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("CHECKING AR PAYMENTS AND ALLOCATIONS")
print("=" * 70)

# Check AR Payments
cursor.execute('SELECT COUNT(*) FROM ar_arpayment')
payment_count = cursor.fetchone()[0]
print(f"\nTotal AR Payments: {payment_count}")

if payment_count > 0:
    cursor.execute('''
        SELECT id, customer_id, reference, date, total_amount, posted_at
        FROM ar_arpayment
        ORDER BY date DESC
    ''')
    payments = cursor.fetchall()
    
    print("\nAR Payments:")
    for payment in payments:
        pay_id, cust_id, ref, date, total, posted = payment
        print(f"\n  Payment ID: {pay_id}")
        print(f"    Reference: {ref}")
        print(f"    Customer ID: {cust_id}")
        print(f"    Date: {date}")
        print(f"    Amount: ${total}")
        print(f"    Posted: {posted or 'Not posted'}")
        
        # Check allocations for this payment
        cursor.execute('''
            SELECT invoice_id, amount
            FROM ar_arpaymentallocation
            WHERE payment_id = ?
        ''', (pay_id,))
        allocations = cursor.fetchall()
        
        if allocations:
            print(f"    Allocations:")
            for alloc in allocations:
                inv_id, amount = alloc
                print(f"      - Invoice ID {inv_id}: ${amount}")
        else:
            print(f"    Allocations: None")

# Check payment allocation totals per invoice
print("\n" + "=" * 70)
print("PAYMENT ALLOCATIONS BY INVOICE")
print("=" * 70)

cursor.execute('''
    SELECT 
        a.invoice_id,
        i.number,
        i.payment_status,
        SUM(a.amount) as total_paid
    FROM ar_arpaymentallocation a
    JOIN ar_arinvoice i ON a.invoice_id = i.id
    GROUP BY a.invoice_id, i.number, i.payment_status
''')

allocations_by_invoice = cursor.fetchall()

if allocations_by_invoice:
    print("\nInvoices with Payment Allocations:")
    for row in allocations_by_invoice:
        inv_id, inv_num, status, total_paid = row
        print(f"\n  Invoice #{inv_num} (ID: {inv_id})")
        print(f"    Current Status: {status}")
        print(f"    Total Paid: ${total_paid}")
        
        # Calculate total and outstanding
        cursor.execute('''
            SELECT quantity, unit_price, tax_rate_id
            FROM ar_aritem
            WHERE invoice_id = ?
        ''', (inv_id,))
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
        
        outstanding = total - Decimal(str(total_paid))
        
        print(f"    Invoice Total: ${total}")
        print(f"    Outstanding: ${outstanding}")
        
        # Determine correct status
        if outstanding <= 0:
            correct_status = "PAID"
        elif Decimal(str(total_paid)) > 0:
            correct_status = "PARTIALLY_PAID"
        else:
            correct_status = "UNPAID"
        
        if status != correct_status:
            print(f"    ⚠️ STATUS MISMATCH! Should be: {correct_status}")
        else:
            print(f"    ✓ Status is correct")
else:
    print("\nNo payment allocations found.")

conn.close()

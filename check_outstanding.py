import sqlite3
from decimal import Decimal

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("CHECKING OUTSTANDING INVOICE BALANCES")
print("=" * 70)

# Get invoice details with items
cursor.execute('''
    SELECT 
        i.id, 
        i.number, 
        i.customer_id,
        i.date,
        i.is_posted,
        i.is_cancelled
    FROM ar_arinvoice i
    WHERE i.is_posted = 1 AND i.is_cancelled = 0
''')

invoices = cursor.fetchall()

print(f"\nFound {len(invoices)} posted, non-cancelled invoice(s)\n")

for inv in invoices:
    inv_id, number, customer_id, date, is_posted, is_cancelled = inv
    
    # Get customer name
    cursor.execute('SELECT name FROM ar_customer WHERE id = ?', (customer_id,))
    customer = cursor.fetchone()
    customer_name = customer[0] if customer else "Unknown"
    
    # Calculate total from items
    cursor.execute('''
        SELECT 
            quantity,
            unit_price,
            tax_rate_id
        FROM ar_aritem
        WHERE invoice_id = ?
    ''', (inv_id,))
    
    items = cursor.fetchall()
    
    total = Decimal('0.00')
    print(f"Invoice #{number} (ID: {inv_id})")
    print(f"  Customer: {customer_name} (ID: {customer_id})")
    print(f"  Date: {date}")
    print(f"  Items: {len(items)}")
    
    for item in items:
        qty, price, tax_rate_id = item
        qty = Decimal(str(qty))
        price = Decimal(str(price))
        subtotal = qty * price
        
        # Get tax rate if applicable
        tax_amount = Decimal('0.00')
        if tax_rate_id:
            cursor.execute('SELECT rate FROM core_taxrate WHERE id = ?', (tax_rate_id,))
            tax_rate = cursor.fetchone()
            if tax_rate:
                tax_rate_val = Decimal(str(tax_rate[0]))
                tax_amount = subtotal * (tax_rate_val / 100)
        
        item_total = subtotal + tax_amount
        total += item_total
        print(f"    Qty: {qty}, Price: {price}, Subtotal: {subtotal}, Tax: {tax_amount}, Total: {item_total}")
    
    # Get paid amount
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM ar_arpaymentallocation
        WHERE invoice_id = ?
    ''', (inv_id,))
    
    paid = cursor.fetchone()[0]
    paid = Decimal(str(paid)) if paid else Decimal('0.00')
    
    outstanding = total - paid
    
    print(f"  Invoice Total: ${total:.2f}")
    print(f"  Paid Amount: ${paid:.2f}")
    print(f"  Outstanding: ${outstanding:.2f}")
    
    if outstanding > 0:
        print(f"  ✅ This invoice SHOULD appear in payment screen")
    else:
        print(f"  ❌ This invoice will NOT appear (fully paid or zero balance)")
    print()

conn.close()

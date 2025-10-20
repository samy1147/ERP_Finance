import sqlite3
from decimal import Decimal

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=" * 70)
print("CHECKING AP INVOICES AND OUTSTANDING BALANCES")
print("=" * 70)

# Get AP invoice details
cursor.execute('''
    SELECT 
        i.id, 
        i.number, 
        i.supplier_id,
        i.date,
        i.is_posted,
        i.is_cancelled,
        i.payment_status
    FROM ap_apinvoice i
    WHERE i.is_posted = 1 AND i.is_cancelled = 0
''')

invoices = cursor.fetchall()

print(f"\nFound {len(invoices)} posted, non-cancelled AP invoice(s)\n")

for inv in invoices:
    inv_id, number, supplier_id, date, is_posted, is_cancelled, payment_status = inv
    
    # Get supplier name
    cursor.execute('SELECT name FROM ap_supplier WHERE id = ?', (supplier_id,))
    supplier = cursor.fetchone()
    supplier_name = supplier[0] if supplier else "Unknown"
    
    # Calculate total from items
    cursor.execute('''
        SELECT 
            quantity,
            unit_price,
            tax_rate_id
        FROM ap_apitem
        WHERE invoice_id = ?
    ''', (inv_id,))
    
    items = cursor.fetchall()
    
    total = Decimal('0.00')
    print(f"Invoice #{number} (ID: {inv_id})")
    print(f"  Supplier: {supplier_name} (ID: {supplier_id})")
    print(f"  Date: {date}")
    print(f"  Payment Status: {payment_status}")
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
        FROM ap_appaymentallocation
        WHERE invoice_id = ?
    ''', (inv_id,))
    
    paid = cursor.fetchone()[0]
    paid = Decimal(str(paid)) if paid else Decimal('0.00')
    
    outstanding = total - paid
    
    print(f"  Invoice Total: ${total:.2f}")
    print(f"  Paid Amount: ${paid:.2f}")
    print(f"  Outstanding: ${outstanding:.2f}")
    
    if outstanding > 0:
        print(f"  ✅ This invoice SHOULD appear in AP payment screen")
    else:
        print(f"  ❌ This invoice will NOT appear (fully paid or zero balance)")
    print()

# Check suppliers
print("=" * 70)
print("SUPPLIERS")
print("=" * 70)

cursor.execute('SELECT id, code, name FROM ap_supplier')
suppliers = cursor.fetchall()

print(f"\nTotal Suppliers: {len(suppliers)}\n")
for supp in suppliers:
    print(f"Supplier ID: {supp[0]}, Code: {supp[1]}, Name: {supp[2]}")

conn.close()

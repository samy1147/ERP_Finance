import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check AR Invoices
print("=" * 60)
print("AR INVOICES STATUS")
print("=" * 60)

cursor.execute('''
    SELECT id, number, customer_id, date, is_posted, is_cancelled 
    FROM ar_arinvoice
''')
rows = cursor.fetchall()

print(f"\nTotal AR Invoices: {len(rows)}\n")

for row in rows:
    inv_id, number, customer_id, date, is_posted, is_cancelled = row
    print(f"Invoice ID: {inv_id}")
    print(f"  Number: {number}")
    print(f"  Customer ID: {customer_id}")
    print(f"  Date: {date}")
    print(f"  Posted: {'Yes' if is_posted else 'No'}")
    print(f"  Cancelled: {'Yes' if is_cancelled else 'No'}")
    print()

# Check customers
print("=" * 60)
print("CUSTOMERS")
print("=" * 60)

cursor.execute('SELECT id, code, name FROM ar_customer')
customers = cursor.fetchall()

print(f"\nTotal Customers: {len(customers)}\n")
for cust in customers:
    print(f"Customer ID: {cust[0]}, Code: {cust[1]}, Name: {cust[2]}")

# Check payment allocations
print("\n" + "=" * 60)
print("PAYMENT ALLOCATIONS")
print("=" * 60)

cursor.execute('''
    SELECT invoice_id, SUM(amount) as total_paid
    FROM ar_arpaymentallocation
    GROUP BY invoice_id
''')
allocations = cursor.fetchall()

if allocations:
    print(f"\nPayments Applied to Invoices:\n")
    for alloc in allocations:
        print(f"  Invoice ID {alloc[0]}: ${alloc[1]} paid")
else:
    print("\nNo payment allocations found.")

conn.close()

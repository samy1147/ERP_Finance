import sqlite3

db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== ap_invoice_distribution Foreign Keys ===")
cursor.execute("PRAGMA foreign_key_list(ap_invoice_distribution)")
fks = cursor.fetchall()
for fk in fks:
    print(f"  Column: {fk[3]:20} -> Table: {fk[2]:30} Column: {fk[4]}")

print("\n=== ap_invoice_distribution_segment Foreign Keys ===")
cursor.execute("PRAGMA foreign_key_list(ap_invoice_distribution_segment)")
fks = cursor.fetchall()
for fk in fks:
    print(f"  Column: {fk[3]:20} -> Table: {fk[2]:30} Column: {fk[4]}")

conn.close()
print("\n✅ Foreign key verification complete!")

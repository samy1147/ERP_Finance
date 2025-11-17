import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]

print(f'Total tables in database: {len(tables)}')

# Find invoice-related tables
invoice_tables = [t for t in tables if 'invoice' in t.lower()]
print(f'\nInvoice-related tables ({len(invoice_tables)}):')
for t in invoice_tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    count = cur.fetchone()[0]
    print(f'  - {t}: {count} records')

# Verify deprecated tables are gone
deprecated = ['finance_invoice', 'finance_invoiceline', 'finance_taxcode']
missing = [t for t in deprecated if t not in tables]
print(f'\nDeprecated tables removed: {len(missing)}/{len(deprecated)}')
for t in missing:
    print(f'  ✓ {t} (removed)')

conn.close()

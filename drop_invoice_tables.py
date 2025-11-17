import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Disable foreign key constraints temporarily
cur.execute('PRAGMA foreign_keys=OFF')

# Drop the deprecated tables
cur.execute('DROP TABLE IF EXISTS finance_invoice')
cur.execute('DROP TABLE IF EXISTS finance_invoiceline')
cur.execute('DROP TABLE IF EXISTS finance_taxcode')

conn.commit()
print('Successfully dropped deprecated tables: finance_invoice, finance_invoiceline, finance_taxcode')

# Re-enable foreign key constraints
cur.execute('PRAGMA foreign_keys=ON')

# Verify tables are gone
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'finance_%' ORDER BY name")
remaining = [r[0] for r in cur.fetchall()]
print(f'\nRemaining finance tables ({len(remaining)}): {remaining}')

conn.close()

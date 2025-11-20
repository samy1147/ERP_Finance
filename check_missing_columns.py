import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get actual columns
cursor.execute('PRAGMA table_info(assets_asset)')
existing_columns = {col[1] for col in cursor.fetchall()}

# Expected foreign key columns from the model
expected_fk_columns = {
    'capitalization_journal_id',
    'disposal_journal_id', 
    'currency_id',
    'category_id',
    'created_by_id',
    'supplier_id',
    'depreciation_expense_account_id',
    'location_id',
    'ap_invoice_id',
    'grn_id',
    'grn_line_id'
}

missing = expected_fk_columns - existing_columns
print("Missing columns:")
for col in sorted(missing):
    print(f"  - {col}")

print("\nExisting columns:")
for col in sorted(existing_columns):
    print(f"  - {col}")

conn.close()

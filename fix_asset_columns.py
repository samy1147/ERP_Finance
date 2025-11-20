"""
Script to add missing columns to assets_asset table
This fixes the database schema to match the Django models
"""
import sqlite3

def add_missing_columns():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute('PRAGMA table_info(assets_asset)')
    existing_columns = {col[1] for col in cursor.fetchall()}
    
    # Define columns to add (nullable foreign keys)
    columns_to_add = [
        ('capitalization_journal_id', 'INTEGER NULL REFERENCES finance_journalentry(id)'),
        ('disposal_journal_id', 'INTEGER NULL REFERENCES finance_journalentry(id)'),
        ('currency_id', 'INTEGER NULL REFERENCES core_currency(id)'),
        ('category_id', 'INTEGER NULL REFERENCES assets_category(id)'),
        ('created_by_id', 'INTEGER NULL REFERENCES auth_user(id)'),
        ('supplier_id', 'INTEGER NULL REFERENCES ap_supplier(id)'),
        ('depreciation_expense_account_id', 'INTEGER NULL REFERENCES segment_xx_segment(id)'),
        ('ap_invoice_id', 'INTEGER NULL REFERENCES ap_apinvoice(id)'),
        ('ap_invoice_line', 'INTEGER NULL'),
        ('grn_id', 'INTEGER NULL REFERENCES receiving_goodsreceipt(id)'),
        ('grn_line_id', 'INTEGER NULL REFERENCES receiving_grnline(id)'),
        ('source_type', "VARCHAR(20) DEFAULT 'MANUAL'"),
    ]
    
    added_count = 0
    skipped_count = 0
    
    for col_name, col_def in columns_to_add:
        if col_name in existing_columns:
            print(f"Skipping {col_name} - already exists")
            skipped_count += 1
            continue
        
        try:
            sql = f"ALTER TABLE assets_asset ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            print(f"✓ Added column: {col_name}")
            added_count += 1
        except sqlite3.OperationalError as e:
            print(f"✗ Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\nSummary:")
    print(f"  Added: {added_count} columns")
    print(f"  Skipped: {skipped_count} columns (already exist)")
    print(f"\nDatabase schema updated successfully!")

if __name__ == '__main__':
    add_missing_columns()

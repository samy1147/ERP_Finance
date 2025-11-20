import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all assets tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'assets_%' ORDER BY name")
existing_tables = [row[0] for row in cursor.fetchall()]

print("Existing assets tables:")
for table in existing_tables:
    print(f"  - {table}")

# Expected tables based on models
expected_tables = [
    'assets_asset',
    'assets_category',
    'assets_location',
    'assets_document',
    'assets_configuration',
    'assets_depreciation',
    'assets_transfer',
    'assets_disposal',
    'assets_adjustment',
    'assets_retirement',
]

print("\nMissing tables:")
for table in expected_tables:
    if table not in existing_tables:
        print(f"  - {table}")

conn.close()

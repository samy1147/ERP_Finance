import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all procurement tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'procurement_%' ORDER BY name")
existing_tables = [row[0] for row in cursor.fetchall()]

print("Existing procurement tables:")
for table in existing_tables:
    print(f"  - {table}")

# Get all receiving tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'receiving_%' ORDER BY name")
receiving_tables = [row[0] for row in cursor.fetchall()]

print("\nExisting receiving tables:")
for table in receiving_tables:
    print(f"  - {table}")

conn.close()

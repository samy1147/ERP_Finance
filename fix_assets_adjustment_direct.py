import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Disable foreign key checks
cursor.execute("PRAGMA foreign_keys = OFF")

# Drop and recreate assets_adjustment table
cursor.execute("DROP TABLE IF EXISTS assets_adjustment")
cursor.execute("""
    CREATE TABLE assets_adjustment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        adjustment_date DATE NOT NULL,
        adjustment_type VARCHAR(20) NOT NULL,
        old_cost DECIMAL(15, 2),
        new_cost DECIMAL(15, 2),
        cost_difference DECIMAL(15, 2),
        old_useful_life DECIMAL(5, 2),
        new_useful_life DECIMAL(5, 2),
        depreciation_adjustment_amount DECIMAL(15, 2),
        old_category_id INTEGER,
        new_category_id INTEGER,
        reason TEXT NOT NULL,
        notes TEXT,
        approval_status VARCHAR(20) DEFAULT 'DRAFT',
        submitted_by_id INTEGER,
        submitted_at DATETIME,
        approved_by_id INTEGER,
        approved_at DATETIME,
        approval_notes TEXT,
        is_posted BOOLEAN DEFAULT 0,
        journal_entry_id INTEGER,
        posted_at DATETIME,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        created_by_id INTEGER
    )
""")

conn.commit()

# Re-enable foreign key checks
cursor.execute("PRAGMA foreign_keys = ON")

conn.close()

print("✓ Fixed assets_adjustment table")

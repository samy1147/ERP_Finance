# Generated manually to create missing tables
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fixed_assets', '0010_add_missing_asset_columns'),
    ]
    
    # Disable atomic to run outside transaction
    atomic = False

    operations = [
        migrations.RunSQL(
            sql=[
                # Disable foreign key checks
                "PRAGMA foreign_keys = OFF;",
            ],
            reverse_sql=["PRAGMA foreign_keys = ON;"],
        ),
        
        # Create assets_retirement table
        migrations.RunSQL(
            sql=["""
                CREATE TABLE IF NOT EXISTS assets_retirement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    retirement_date DATE NOT NULL,
                    retirement_type VARCHAR(20) NOT NULL,
                    net_book_value_at_retirement DECIMAL(15, 2) NOT NULL,
                    disposal_proceeds DECIMAL(15, 2) DEFAULT 0.00,
                    disposal_costs DECIMAL(15, 2) DEFAULT 0.00,
                    gain_loss DECIMAL(15, 2) DEFAULT 0.00,
                    buyer_recipient VARCHAR(255),
                    sale_invoice_number VARCHAR(100),
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
                );
            """],
            reverse_sql=["DROP TABLE IF EXISTS assets_retirement;"],
        ),
        
        # Create assets_adjustment table
        migrations.RunSQL(
            sql=["""
                CREATE TABLE IF NOT EXISTS assets_adjustment (
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
                );
            """],
            reverse_sql=["DROP TABLE IF EXISTS assets_adjustment;"],
        ),
        
        # Create assets_disposal table (if needed separately)
        migrations.RunSQL(
            sql=["""
                CREATE TABLE IF NOT EXISTS assets_disposal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    disposal_date DATE NOT NULL,
                    disposal_type VARCHAR(20) NOT NULL,
                    disposal_value DECIMAL(15, 2) DEFAULT 0.00,
                    disposal_cost DECIMAL(15, 2) DEFAULT 0.00,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    created_by_id INTEGER
                );
            """],
            reverse_sql=["DROP TABLE IF EXISTS assets_disposal;"],
        ),
        
        # Re-enable foreign key checks
        migrations.RunSQL(
            sql=["PRAGMA foreign_keys = ON;"],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

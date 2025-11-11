"""
Direct SQL script to populate Asset table
Run with: python populate_assets_sql.py
"""

import sqlite3
from datetime import date, timedelta
from decimal import Decimal

def populate_assets_sql():
    """Populate assets using direct SQL to bypass FK constraints"""
    
    print("=" * 60)
    print("   ASSET TABLE POPULATION (SQL)")
    print("=" * 60)
    print()
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Disable foreign key checks
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        print("🔍 Checking existing data...")
        
        # Check if we have categories and locations
        cursor.execute("SELECT COUNT(*) FROM assets_category")
        cat_count = cursor.fetchone()[0]
        print(f"   Found {cat_count} categories")
        
        cursor.execute("SELECT COUNT(*) FROM assets_location")
        loc_count = cursor.fetchone()[0]
        print(f"   Found {loc_count} locations")
        
        if cat_count == 0 or loc_count == 0:
            print("\n⚠️  Warning: Categories or Locations not found!")
            print("   Please create categories and locations first.")
            return
        
        # Get first category and location IDs
        cursor.execute("SELECT id FROM assets_category LIMIT 1")
        category_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM assets_location LIMIT 1")
        location_id = cursor.fetchone()[0]
        
        # Get currency ID (assuming USD exists)
        cursor.execute("SELECT id FROM core_currency WHERE code = 'USD' LIMIT 1")
        currency_result = cursor.fetchone()
        if currency_result:
            currency_id = currency_result[0]
        else:
            print("   Creating USD currency...")
            cursor.execute("""
                INSERT INTO core_currency (code, name, symbol, is_active, created_at, updated_at)
                VALUES ('USD', 'US Dollar', '$', 1, datetime('now'), datetime('now'))
            """)
            currency_id = cursor.lastrowid
        
        print(f"   Using category_id: {category_id}, location_id: {location_id}, currency_id: {currency_id}")
        
        print("\n📦 Creating sample assets...")
        
        # Sample assets data (asset_number, name, description, serial, cost, useful_life_years, status)
        assets_data = [
            ('ASSET-001', 'Dell Laptop XPS 15', 'High-performance laptop', 'DL-XPS-001', 2500.00, 3, 'CAPITALIZED'),
            ('ASSET-002', 'HP Printer LaserJet Pro', 'Office printer', 'HP-LJ-002', 850.00, 5, 'CAPITALIZED'),
            ('ASSET-003', 'Executive Desk - Oak', 'Premium oak desk', 'DESK-OAK-001', 1200.00, 7, 'CAPITALIZED'),
            ('ASSET-004', 'Office Chair - Ergonomic', 'Ergonomic chair', 'CHAIR-ERG-001', 450.00, 5, 'CIP'),
            ('ASSET-005', 'Toyota Hilux 2024', 'Company vehicle', 'TOY-HIL-001', 45000.00, 5, 'CAPITALIZED'),
            ('ASSET-006', 'MacBook Pro 16"', 'Apple laptop', 'MBP-16-001', 3200.00, 3, 'CAPITALIZED'),
            ('ASSET-007', 'Conference Table', 'Meeting room table', 'CONF-TBL-001', 2800.00, 7, 'CAPITALIZED'),
            ('ASSET-008', 'Industrial Forklift', 'Warehouse forklift', 'FORK-IND-001', 28000.00, 10, 'CAPITALIZED'),
            ('ASSET-009', 'Server Rack Dell', 'IT infrastructure', 'SRV-PE-001', 8500.00, 5, 'CAPITALIZED'),
            ('ASSET-010', 'AC Unit 5 Ton', 'Central AC', 'AC-5TON-001', 6500.00, 10, 'CAPITALIZED'),
            ('ASSET-011', 'Excavator CAT 320', 'Construction equipment', 'EXC-CAT-001', 125000.00, 10, 'CIP'),
            ('ASSET-012', 'Standing Desk Electric', 'Adjustable desk', 'DESK-ELEC-001', 750.00, 5, 'CIP'),
        ]
        
        created_count = 0
        
        for asset in assets_data:
            asset_number, name, description, serial, cost, useful_life_years, status = asset
            
            # Check if asset already exists
            cursor.execute("SELECT id FROM assets_asset WHERE asset_number = ?", (asset_number,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"↻ Skipping (exists): {asset_number}")
                continue
            
            # Calculate dates
            days_ago = 30 if status == 'CIP' else 180
            acq_date = (date.today() - timedelta(days=days_ago)).isoformat()
            cap_date = acq_date if status == 'CAPITALIZED' else None
            # Set depreciation_start_date to acquisition_date for both CIP and CAPITALIZED
            dep_start = acq_date
            
            # Insert asset
            cursor.execute("""
                INSERT INTO assets_asset (
                    asset_number, name, description, serial_number,
                    category_id, location_id, currency_id,
                    acquisition_date, acquisition_cost, useful_life_years,
                    status, capitalization_date, depreciation_start_date,
                    total_depreciation, net_book_value, depreciation_method,
                    salvage_value, disposal_method, purchase_order, notes, disposal_notes,
                    created_at, updated_at, source_type, accumulated_depreciation_account_id,
                    asset_account_id, depreciation_expense_account_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'MANUAL', 1, 1, 1)
            """, (
                asset_number, name, description, serial,
                category_id, location_id, currency_id,
                acq_date, cost, useful_life_years,
                status, cap_date, dep_start,
                0.00, cost, 'STRAIGHT_LINE',
                0.00, '', '', '', ''
            ))
            
            created_count += 1
            print(f"✓ Created: {asset_number} - {name} ({status})")
        
        # Commit changes
        conn.commit()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM assets_asset")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets_asset WHERE status = 'CIP'")
        cip_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets_asset WHERE status = 'CAPITALIZED'")
        cap_count = cursor.fetchone()[0]
        
        print(f"\n✅ Asset population complete!")
        print(f"   Created: {created_count} new assets")
        print(f"   Total: {total} assets in database")
        print(f"\n📊 Asset Summary:")
        print(f"   CIP: {cip_count}")
        print(f"   CAPITALIZED: {cap_count}")
        
        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("   SUCCESS!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    populate_assets_sql()

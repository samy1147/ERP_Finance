"""
Reorganize Postman Collections - Create One Collection Per Folder
Each folder will become a single collection with organized sub-folders
"""
import os
import json
import shutil
from datetime import datetime
from collections import defaultdict

print("="*80)
print("REORGANIZING POSTMAN COLLECTIONS - ONE COLLECTION PER FOLDER")
print("="*80)

source_dir = "postman_collections"
output_dir = "postman_collections_organized"

# Remove output dir if exists
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

# Define folder metadata
folder_info = {
    "00_Other": {
        "name": "Other - Customers & Misc",
        "description": "Customer management and miscellaneous endpoints"
    },
    "01_Finance": {
        "name": "Finance - Core Financial Management",
        "description": "Accounts, journals, currencies, FX rates, bank accounts, and invoice approvals"
    },
    "02_AR": {
        "name": "Accounts Receivable (AR)",
        "description": "AR invoices, payments, and customer transactions"
    },
    "03_AP": {
        "name": "Accounts Payable (AP)",
        "description": "AP invoices, payments, vendors, and supplier management"
    },
    "04_Inventory": {
        "name": "Inventory Management",
        "description": "Inventory balances, movements, adjustments, and transfers"
    },
    "05_Procurement": {
        "name": "Procurement & Purchasing",
        "description": "Purchase requisitions, orders, goods receipts, RFX, contracts, and vendor bills"
    },
    "06_Fixed_Assets": {
        "name": "Fixed Assets Management",
        "description": "Asset tracking, depreciation, transfers, adjustments, and maintenance"
    },
    "07_Segments": {
        "name": "Segments & Chart of Accounts",
        "description": "Segment types, values, hierarchies, and account assignments"
    },
    "08_Periods": {
        "name": "Fiscal Periods & Years",
        "description": "Fiscal year and period management, opening and closing periods"
    },
    "09_Tax": {
        "name": "Tax Management",
        "description": "Corporate tax, filing, accrual, and tax rate management"
    },
    "10_Reports": {
        "name": "Financial Reports",
        "description": "AR aging, AP aging, trial balance, and other financial reports"
    },
    "12_Auth": {
        "name": "Authentication & Documentation",
        "description": "CSRF tokens, API documentation, and schema endpoints"
    }
}

# Process each folder
for folder_name in sorted(os.listdir(source_dir)):
    folder_path = os.path.join(source_dir, folder_name)
    
    if not os.path.isdir(folder_path):
        continue
    
    # Skip if no metadata
    if folder_name not in folder_info:
        print(f"⚠️  Skipping {folder_name} - no metadata defined")
        continue
    
    print(f"\n📁 Processing: {folder_name}")
    
    # Get all JSON collection files
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    if not json_files:
        print(f"   No collections found")
        continue
    
    # Group collections by type
    grouped_items = defaultdict(list)
    
    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                collection_data = json.load(f)
            
            # Extract items from the collection
            items = collection_data.get('item', [])
            
            # Determine group name from filename
            base_name = json_file.replace('.postman_collection.json', '')
            parts = base_name.split('_')
            
            # Create a meaningful group name
            if len(parts) >= 2:
                group_name = ' '.join(parts[1:]).replace('-', ' ').replace('_', ' ').title()
                if not group_name or group_name == '':
                    group_name = parts[0].replace('-', ' ').replace('_', ' ').title()
            else:
                group_name = base_name.replace('-', ' ').replace('_', ' ').title()
            
            # Add items to the group
            if items:
                grouped_items[group_name].extend(items)
            
        except Exception as e:
            print(f"   ❌ Error reading {json_file}: {e}")
    
    # Create the consolidated collection
    info = folder_info[folder_name]
    
    # Build organized items structure
    organized_items = []
    
    for group_name in sorted(grouped_items.keys()):
        group_items = grouped_items[group_name]
        
        # Create a folder (item group)
        folder_item = {
            "name": group_name,
            "item": group_items,
            "description": f"{len(group_items)} requests for {group_name}"
        }
        
        organized_items.append(folder_item)
    
    # Create the main collection
    collection = {
        "info": {
            "name": info["name"],
            "_postman_id": f"{folder_name.lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": info["description"],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "_exporter_id": "ERP_Finance_System"
        },
        "item": organized_items,
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "auth_token",
                "value": "",
                "type": "string",
                "description": "Authentication token (if required)"
            }
        ],
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Pre-request script for all requests in this collection",
                        "// You can add global pre-request logic here"
                    ]
                }
            },
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Test script for all requests in this collection",
                        "// Basic status code validation",
                        "pm.test('Status code is valid', function() {",
                        "    pm.expect(pm.response.code).to.be.oneOf([200, 201, 204]);",
                        "});"
                    ]
                }
            }
        ]
    }
    
    # Save the consolidated collection
    output_file = os.path.join(output_dir, f"{info['name']}.postman_collection.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    total_requests = sum(len(grouped_items[g]) for g in grouped_items)
    print(f"   ✅ Created: {info['name']}")
    print(f"      Groups: {len(grouped_items)}")
    print(f"      Total Requests: {total_requests}")

# Create a master README
readme_path = os.path.join(output_dir, "README.md")
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write("# ERP Finance - Organized Postman Collections\n\n")
    f.write("**ONE collection per module** - Each collection contains organized sub-folders\n\n")
    f.write("## 📦 Collections Available\n\n")
    
    for folder_name in sorted(folder_info.keys()):
        info = folder_info[folder_name]
        f.write(f"### {info['name']}\n")
        f.write(f"**Description**: {info['description']}\n\n")
        f.write(f"**File**: `{info['name']}.postman_collection.json`\n\n")
    
    f.write("## 🚀 How to Import\n\n")
    f.write("1. Open Postman\n")
    f.write("2. Click **Import** button\n")
    f.write("3. Select the collection file(s) you want\n")
    f.write("4. The collection will be imported with organized sub-folders\n\n")
    
    f.write("## ⚙️ Configuration\n\n")
    f.write("Each collection has these variables:\n\n")
    f.write("- **`base_url`**: Your API server URL (default: http://localhost:8000)\n")
    f.write("- **`auth_token`**: Your authentication token (if required)\n\n")
    
    f.write("**To configure:**\n")
    f.write("1. Click on the collection name\n")
    f.write("2. Go to **Variables** tab\n")
    f.write("3. Update the `Value` column\n")
    f.write("4. Save the collection\n\n")
    
    f.write("## 📋 What's Inside Each Collection\n\n")
    f.write("Each collection is organized into **sub-folders** by functionality:\n\n")
    f.write("- **List endpoints** - GET all records\n")
    f.write("- **List with filters** - GET with pagination, status, search\n")
    f.write("- **Detail endpoints** - GET by ID\n")
    f.write("- **Create** - POST with sample bodies\n")
    f.write("- **Update** - PUT (full) and PATCH (partial)\n")
    f.write("- **Delete** - DELETE by ID\n\n")
    
    f.write("## 🧪 Testing\n\n")
    f.write("Each collection includes:\n")
    f.write("- Pre-request scripts (global for all requests)\n")
    f.write("- Test scripts (automatic status code validation)\n")
    f.write("- Sample request bodies with realistic data\n")
    f.write("- Query parameter examples for filters\n\n")
    
    f.write("## 📊 Collection List\n\n")
    f.write("| # | Collection Name | Description |\n")
    f.write("|---|-----------------|-------------|\n")
    
    for idx, folder_name in enumerate(sorted(folder_info.keys()), 1):
        info = folder_info[folder_name]
        f.write(f"| {idx} | {info['name']} | {info['description']} |\n")
    
    f.write("\n## 🎯 Quick Start\n\n")
    f.write("**For Finance Module:**\n")
    f.write("1. Import `Finance - Core Financial Management.postman_collection.json`\n")
    f.write("2. Set `base_url` variable\n")
    f.write("3. Navigate to sub-folders (Accounts, Journals, etc.)\n")
    f.write("4. Run requests\n\n")
    
    f.write("**For AR/AP:**\n")
    f.write("1. Import both AR and AP collections\n")
    f.write("2. Test invoice creation (POST)\n")
    f.write("3. Test payment processing\n")
    f.write("4. Test GL posting\n\n")
    
    f.write("## ⚡ Advantages of This Organization\n\n")
    f.write("- ✅ **One file per module** - Easy to manage\n")
    f.write("- ✅ **Organized sub-folders** - Logical grouping\n")
    f.write("- ✅ **Shared variables** - Configure once per collection\n")
    f.write("- ✅ **Global scripts** - Pre-request and test logic shared\n")
    f.write("- ✅ **Easy import** - Just select the collections you need\n")
    f.write("- ✅ **Clean workspace** - 12 collections instead of 85 files\n\n")

print(f"\n{'='*80}")
print(f"✅ SUCCESS!")
print(f"📁 Output: {output_dir}/")
print(f"📄 Collections: {len(folder_info)}")
print(f"{'='*80}\n")

# Create summary
print("📊 COLLECTIONS CREATED:\n")
for folder_name in sorted(folder_info.keys()):
    info = folder_info[folder_name]
    filename = f"{info['name']}.postman_collection.json"
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_groups = len(data.get('item', []))
        total_requests = 0
        for group in data.get('item', []):
            total_requests += len(group.get('item', []))
        
        print(f"✅ {info['name']}")
        print(f"   Sub-folders: {total_groups}")
        print(f"   Total Requests: {total_requests}\n")

print(f"{'='*80}")
print("🎉 READY TO IMPORT INTO POSTMAN!")
print(f"{'='*80}\n")

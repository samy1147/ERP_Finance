"""
Reorganize Postman Collections into App Folders
Clean up and consolidate collections
"""
import os
import json
import shutil
from collections import defaultdict

print("="*80)
print("REORGANIZING POSTMAN COLLECTIONS")
print("="*80)

# Create main folders structure
base_dir = "postman_collections"
if os.path.exists(base_dir):
    shutil.rmtree(base_dir)
os.makedirs(base_dir)

# Define app groupings
app_structure = {
    "01_Finance": ["currencies", "accounts", "journals", "journal-lines", "bank-accounts", "fx", "invoice-approvals"],
    "02_AR": ["ar"],
    "03_AP": ["ap"],
    "04_Inventory": ["inventory"],
    "05_Procurement": ["procurement"],
    "06_Fixed_Assets": ["fixed-assets"],
    "07_Segments": ["segment"],
    "08_Periods": ["periods"],
    "09_Tax": ["tax"],
    "10_Reports": ["reports"],
    "11_CRM": ["crm"],
    "12_Auth": ["csrf", "docs", "schema", "redoc"],
}

# Read all generated collections
source_dir = "postman_collections_v2"
all_files = [f for f in os.listdir(source_dir) if f.endswith('.json')]

print(f"\nFound {len(all_files)} collection files")
print("\nOrganizing into folders...\n")

# Group files by app
app_collections = defaultdict(list)

for filename in all_files:
    # Skip format suffix collections
    if '___format' in filename:
        continue
    
    # Determine which app folder this belongs to
    app_found = False
    for folder, apps in app_structure.items():
        for app in apps:
            if filename.startswith(f"{app}_"):
                app_collections[folder].append(filename)
                app_found = True
                break
        if app_found:
            break
    
    if not app_found:
        app_collections["00_Other"].append(filename)

# Create folders and move files
total_moved = 0
for folder, files in sorted(app_collections.items()):
    folder_path = os.path.join(base_dir, folder)
    os.makedirs(folder_path, exist_ok=True)
    
    print(f"📁 {folder}: {len(files)} collections")
    
    for filename in files:
        src = os.path.join(source_dir, filename)
        dst = os.path.join(folder_path, filename)
        
        # Read and potentially merge similar collections
        with open(src, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Write to new location
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        total_moved += 1

# Create README for each folder
for folder in sorted(app_collections.keys()):
    folder_path = os.path.join(base_dir, folder)
    readme_path = os.path.join(folder_path, "README.md")
    
    files = app_collections[folder]
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# {folder.replace('_', ' ')}\n\n")
        f.write(f"This folder contains {len(files)} Postman collections.\n\n")
        f.write("## Collections\n\n")
        for filename in sorted(files):
            name = filename.replace('.postman_collection.json', '').replace('_', ' ').title()
            f.write(f"- **{name}**\n")
        f.write("\n## Import Instructions\n\n")
        f.write("1. Open Postman\n")
        f.write("2. Click Import button\n")
        f.write("3. Select the collection JSON file(s)\n")
        f.write("4. Set variables:\n")
        f.write("   - `base_url`: http://localhost:8000\n")
        f.write("   - `auth_token`: Your authentication token (optional)\n\n")
        f.write("## Testing\n\n")
        f.write("Each collection includes:\n")
        f.write("- GET requests (list all, with filters, get by ID)\n")
        f.write("- POST requests (create new records)\n")
        f.write("- PUT requests (full update)\n")
        f.write("- PATCH requests (partial update)\n")
        f.write("- DELETE requests (delete records)\n\n")

# Create main README
main_readme = os.path.join(base_dir, "README.md")
with open(main_readme, 'w', encoding='utf-8') as f:
    f.write("# ERP Finance - Postman API Collections\n\n")
    f.write("Complete API testing collections for the ERP Finance system.\n\n")
    f.write("## Quick Start\n\n")
    f.write("1. **Import Collections**: Import the collections you need into Postman\n")
    f.write("2. **Set Variables**:\n")
    f.write("   - `base_url`: http://localhost:8000 (or your server URL)\n")
    f.write("   - `auth_token`: Your authentication token (if required)\n")
    f.write("3. **Start Testing**: Run requests individually or use Collection Runner\n\n")
    f.write("## Folder Structure\n\n")
    
    for folder in sorted(app_collections.keys()):
        files = app_collections[folder]
        f.write(f"### {folder.replace('_', ' ')}\n")
        f.write(f"- **Collections**: {len(files)}\n")
        f.write(f"- **Location**: `{folder}/`\n")
        f.write(f"- **Modules**: {', '.join(set([fn.split('_')[0] for fn in files]))}\n\n")
    
    f.write("## Available HTTP Methods\n\n")
    f.write("Each collection includes requests for:\n\n")
    f.write("- **GET**: Retrieve records (list all, with filters, by ID)\n")
    f.write("- **POST**: Create new records\n")
    f.write("- **PUT**: Full update of existing records\n")
    f.write("- **PATCH**: Partial update of existing records\n")
    f.write("- **DELETE**: Delete records\n\n")
    f.write("## Common Filters\n\n")
    f.write("Most GET requests support these query parameters:\n\n")
    f.write("- `status`: Filter by status (e.g., ACTIVE, DRAFT, POSTED)\n")
    f.write("- `page`: Page number for pagination\n")
    f.write("- `page_size`: Number of records per page\n")
    f.write("- `search`: Search across multiple fields\n")
    f.write("- `ordering`: Sort results (e.g., `-created_at`)\n\n")
    f.write("## Request Bodies\n\n")
    f.write("All POST, PUT, and PATCH requests include sample request bodies with:\n")
    f.write("- Required fields\n")
    f.write("- Sample data\n")
    f.write("- Proper data types\n\n")
    f.write("## Authentication\n\n")
    f.write("Some endpoints require authentication. To use:\n\n")
    f.write("1. Enable the `Authorization` header in the request\n")
    f.write("2. Set `{{auth_token}}` variable to your token\n")
    f.write("3. Format: `Token your-token-here`\n\n")
    f.write("## Collection Details\n\n")
    
    total_collections = sum(len(files) for files in app_collections.values())
    f.write(f"- **Total Collections**: {total_collections}\n")
    f.write(f"- **Total Folders**: {len(app_collections)}\n")
    f.write(f"- **Generated**: {total_moved} collections\n")
    f.write(f"- **Format**: Postman Collection v2.1\n\n")
    f.write("## Support\n\n")
    f.write("For issues or questions:\n")
    f.write("- Check the README in each folder\n")
    f.write("- Review the API documentation at `/api/docs/`\n")
    f.write("- Examine the OpenAPI schema at `/api/schema/`\n")

print(f"\n{'='*80}")
print(f"✅ SUCCESS!")
print(f"📁 Organized {total_moved} collections into {len(app_collections)} folders")
print(f"📍 Location: {base_dir}/")
print(f"{'='*80}\n")

# List folder contents
print("Folder Summary:")
for folder in sorted(app_collections.keys()):
    files = app_collections[folder]
    print(f"  {folder}: {len(files)} collections")

print(f"\n{'='*80}\n")

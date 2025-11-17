"""
Generate Complete Postman Collections - Organized by App
"""
import django
import os
import json
import re
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

BASE_URL = "{{base_url}}"

def get_all_urls(urlpatterns, prefix=''):
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            url_path = prefix + str(pattern.pattern)
            urls.append({
                'path': url_path,
                'name': pattern.name or '',
            })
        elif isinstance(pattern, URLResolver):
            urls.extend(get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
    return urls

def clean_url(url_path):
    """Convert Django URL pattern to Postman format"""
    url_path = re.sub(r'\^', '', url_path)
    url_path = re.sub(r'\$', '', url_path)
    url_path = re.sub(r'\(\?P<(\w+)>[^)]+\)', r':\1', url_path)
    url_path = re.sub(r'<(\w+):(\w+)>', r':\2', url_path)
    url_path = re.sub(r'<(\w+)>', r':\1', url_path)
    return url_path.replace('//', '/')

def create_postman_request(name, method, url, body=None, description=""):
    """Create a Postman request object"""
    request = {
        "name": name,
        "request": {
            "method": method,
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json",
                    "type": "text"
                },
                {
                    "key": "Authorization",
                    "value": "Token {{auth_token}}",
                    "type": "text",
                    "disabled": True
                }
            ],
            "url": {
                "raw": f"{BASE_URL}{url}",
                "host": ["{{base_url}}"],
                "path": [p for p in url.split('/') if p]
            },
            "description": description
        },
        "response": []
    }
    
    if body and method in ['POST', 'PUT', 'PATCH']:
        request["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=2),
            "options": {
                "raw": {
                    "language": "json"
                }
            }
        }
    
    return request

def get_sample_body(endpoint_path):
    """Get sample body based on endpoint"""
    path_lower = endpoint_path.lower()
    
    if 'invoice' in path_lower and 'ap' in path_lower:
        return {
            "supplier": 1,
            "invoice_number": "AP-TEST-001",
            "invoice_date": "2024-11-17",
            "due_date": "2024-12-17",
            "currency": "USD",
            "exchange_rate": "1.00",
            "subtotal": "1000.00",
            "tax_amount": "150.00",
            "total": "1150.00",
            "status": "DRAFT"
        }
    elif 'invoice' in path_lower and 'ar' in path_lower:
        return {
            "customer": 1,
            "invoice_number": "AR-TEST-001",
            "invoice_date": "2024-11-17",
            "due_date": "2024-12-17",
            "currency": "USD",
            "exchange_rate": "1.00",
            "subtotal": "1000.00",
            "tax_amount": "150.00",
            "total": "1150.00",
            "status": "DRAFT"
        }
    elif 'payment' in path_lower and 'ap' in path_lower:
        return {
            "supplier": 1,
            "payment_number": "PAY-AP-TEST-001",
            "payment_date": "2024-11-17",
            "payment_method": "BANK_TRANSFER",
            "currency": "USD",
            "amount": "1000.00",
            "reference": "TEST-REF-001"
        }
    elif 'payment' in path_lower and 'ar' in path_lower:
        return {
            "customer": 1,
            "payment_number": "PAY-AR-TEST-001",
            "payment_date": "2024-11-17",
            "payment_method": "BANK_TRANSFER",
            "currency": "USD",
            "amount": "1000.00",
            "reference": "TEST-REF-001"
        }
    elif 'journal' in path_lower:
        return {
            "journal_date": "2024-11-17",
            "period": 1,
            "description": "Test Journal Entry",
            "lines": []
        }
    elif 'vendor' in path_lower or 'supplier' in path_lower:
        return {
            "code": "VEND-TEST-001",
            "name": "Test Vendor",
            "email": "vendor@test.com",
            "currency": "USD",
            "payment_terms": "NET30"
        }
    elif 'customer' in path_lower:
        return {
            "code": "CUST-TEST-001",
            "name": "Test Customer",
            "email": "customer@test.com",
            "currency": "USD"
        }
    elif 'currency' in path_lower or 'currencies' in path_lower:
        return {
            "code": "EUR",
            "name": "Euro",
            "symbol": "€",
            "is_active": True
        }
    elif 'account' in path_lower and 'bank' not in path_lower:
        return {
            "code": "1000",
            "alias": "Test Account",
            "account_type": "ASSET",
            "is_active": True
        }
    elif 'bank' in path_lower:
        return {
            "account_number": "TEST-BANK-001",
            "bank_name": "Test Bank",
            "currency": "USD",
            "gl_account": 1
        }
    elif 'item' in path_lower:
        return {
            "code": "ITEM-TEST-001",
            "description": "Test Item",
            "unit_of_measure": "EA",
            "is_active": True
        }
    elif 'purchase-requisition' in path_lower or 'pr' in path_lower:
        return {
            "pr_number": "PR-TEST-001",
            "requested_date": "2024-11-17",
            "required_date": "2024-12-01",
            "department": "IT",
            "status": "DRAFT"
        }
    elif 'purchase-order' in path_lower or 'po' in path_lower:
        return {
            "po_number": "PO-TEST-001",
            "supplier": 1,
            "order_date": "2024-11-17",
            "delivery_date": "2024-12-01",
            "currency": "USD",
            "status": "DRAFT"
        }
    elif 'segment' in path_lower and 'type' in path_lower:
        return {
            "segment_type": "DEPARTMENT",
            "segment_name": "Department",
            "is_active": True,
            "is_required": True
        }
    elif 'segment' in path_lower and 'value' in path_lower:
        return {
            "code": "DEPT-TEST",
            "alias": "Test Department",
            "segment_type": 1,
            "is_active": True
        }
    elif 'fiscal-year' in path_lower:
        return {
            "year": 2025,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "is_closed": False
        }
    elif 'fiscal-period' in path_lower or 'period' in path_lower:
        return {
            "period_number": 1,
            "period_name": "January 2025",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "fiscal_year": 1
        }
    elif 'lead' in path_lower:
        return {
            "name": "Test Lead",
            "company": "Test Company",
            "email": "lead@test.com",
            "status": "NEW"
        }
    elif 'opportunit' in path_lower:
        return {
            "name": "Test Opportunity",
            "customer": 1,
            "amount": "50000.00",
            "probability": 75,
            "stage": "PROPOSAL"
        }
    elif 'contact' in path_lower:
        return {
            "first_name": "Test",
            "last_name": "Contact",
            "email": "contact@test.com"
        }
    elif 'asset' in path_lower and 'fixed' in path_lower:
        return {
            "asset_number": "FA-TEST-001",
            "description": "Test Asset",
            "acquisition_date": "2024-11-17",
            "cost": "5000.00"
        }
    
    return {}

print("="*80)
print("GENERATING POSTMAN COLLECTIONS")
print("="*80)

resolver = get_resolver()
all_urls = get_all_urls(resolver.url_patterns)
api_urls = [u for u in all_urls if u['path'].startswith('api/')]

# Filter out format suffixes
api_urls = [u for u in api_urls if '<drf_format_suffix:format>' not in u['path']]

print(f"\nTotal API endpoints found: {len(api_urls)}")

# Group by app
from collections import defaultdict
apps_data = defaultdict(lambda: defaultdict(list))

for url_info in api_urls:
    path = clean_url(url_info['path'])
    name = url_info['name']
    
    # Skip certain patterns
    if not path or path == '/':
        continue
    
    parts = [p for p in path.split('/') if p and not p.startswith(':')]
    
    if len(parts) < 2:
        continue
    
    app = parts[1] if len(parts) > 1 else 'core'
    
    # Determine if it's a detail or list endpoint
    has_id = ':' in path or any(p.startswith(':') for p in path.split('/'))
    
    # Determine subgroup
    if len(parts) > 2:
        subgroup = parts[2]
    else:
        subgroup = 'general'
    
    apps_data[app][subgroup].append({
        'path': path,
        'name': name,
        'is_detail': has_id
    })

print(f"Organized into {len(apps_data)} apps\n")

# Create output directory
os.makedirs('postman_collections_v2', exist_ok=True)

collection_count = 0

for app_name, subgroups in sorted(apps_data.items()):
    for subgroup_name, endpoints in sorted(subgroups.items()):
        collection_name = f"{app_name.upper()} - {subgroup_name.replace('-', ' ').title()}"
        
        items = []
        
        # Process each endpoint
        processed_paths = set()
        
        for endpoint in endpoints:
            path = endpoint['path']
            is_detail = endpoint['is_detail']
            
            # Skip duplicates
            if path in processed_paths:
                continue
            processed_paths.add(path)
            
            # Determine endpoint type from path
            endpoint_type = path.split('/')[-1] if not is_detail else path.split('/')[-2]
            sample_body = get_sample_body(path)
            
            # List endpoint (GET all)
            if not is_detail:
                items.append(create_postman_request(
                    f"List All {endpoint_type.title()}",
                    "GET",
                    path,
                    description=f"Retrieve all {endpoint_type} with optional filters"
                ))
                
                # GET with filters
                filter_path = f"{path}?status=ACTIVE&page=1&page_size=10"
                items.append(create_postman_request(
                    f"List {endpoint_type.title()} (with filters)",
                    "GET",
                    filter_path,
                    description=f"Retrieve {endpoint_type} with status and pagination filters"
                ))
                
                # POST (Create)
                if sample_body:
                    items.append(create_postman_request(
                        f"Create {endpoint_type.title()}",
                        "POST",
                        path,
                        body=sample_body,
                        description=f"Create a new {endpoint_type}"
                    ))
            
            # Detail endpoint (GET/PUT/PATCH/DELETE specific)
            else:
                items.append(create_postman_request(
                    f"Get {endpoint_type.title()} by ID",
                    "GET",
                    path,
                    description=f"Retrieve specific {endpoint_type} by ID"
                ))
                
                # PUT (Full update)
                if sample_body:
                    items.append(create_postman_request(
                        f"Update {endpoint_type.title()} (Full)",
                        "PUT",
                        path,
                        body=sample_body,
                        description=f"Full update of {endpoint_type}"
                    ))
                    
                    # PATCH (Partial update)
                    partial_body = {k: v for i, (k, v) in enumerate(sample_body.items()) if i < 2}
                    items.append(create_postman_request(
                        f"Update {endpoint_type.title()} (Partial)",
                        "PATCH",
                        path,
                        body=partial_body,
                        description=f"Partial update of {endpoint_type}"
                    ))
                
                # DELETE
                items.append(create_postman_request(
                    f"Delete {endpoint_type.title()}",
                    "DELETE",
                    path,
                    description=f"Delete specific {endpoint_type}"
                ))
        
        # Create collection
        collection = {
            "info": {
                "name": collection_name,
                "_postman_id": f"{app_name}-{subgroup_name}-{datetime.now().strftime('%Y%m%d')}",
                "description": f"API endpoints for {collection_name}",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": items,
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "auth_token",
                    "value": "",
                    "type": "string"
                }
            ]
        }
        
        # Save collection
        safe_app = re.sub(r'[^\w\-]', '_', app_name)
        safe_subgroup = re.sub(r'[^\w\-]', '_', subgroup_name)
        filename = f"postman_collections_v2/{safe_app}_{safe_subgroup}.postman_collection.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        collection_count += 1
        print(f"✅ Created: {filename} ({len(items)} requests)")

print(f"\n{'='*80}")
print(f"✅ SUCCESS! Generated {collection_count} Postman collections")
print(f"📁 Location: postman_collections_v2/")
print(f"{'='*80}\n")

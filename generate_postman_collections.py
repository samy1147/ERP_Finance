"""
Generate Comprehensive Postman Collections for All API Endpoints
Organized by app with proper HTTP methods, filters, and bodies
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework import serializers
import json
import re
from collections import defaultdict

def get_all_urls(urlpatterns, prefix=''):
    """Extract all URL patterns"""
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            url_path = prefix + str(pattern.pattern)
            callback = pattern.callback
            
            # Get ViewSet class if it exists
            viewset_class = None
            if hasattr(callback, 'cls'):
                viewset_class = callback.cls
            elif hasattr(callback, 'view_class'):
                viewset_class = callback.view_class
            
            urls.append({
                'path': url_path,
                'name': pattern.name,
                'callback': callback,
                'viewset': viewset_class
            })
        elif isinstance(pattern, URLResolver):
            urls.extend(get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
    return urls

def clean_url_pattern(url_path):
    """Convert Django URL pattern to readable path"""
    # Remove regex anchors
    url_path = re.sub(r'\^', '', url_path)
    url_path = re.sub(r'\$', '', url_path)
    # Convert parameters
    url_path = re.sub(r'\(\?P<(\w+)>[^)]+\)', r':\1', url_path)
    url_path = re.sub(r'<(\w+):(\w+)>', r':\2', url_path)
    return '/' + url_path.replace('//', '/')

def get_http_methods(viewset):
    """Determine which HTTP methods are supported"""
    methods = []
    if viewset:
        if hasattr(viewset, 'list') or hasattr(viewset, 'retrieve'):
            methods.append('GET')
        if hasattr(viewset, 'create'):
            methods.append('POST')
        if hasattr(viewset, 'update') or hasattr(viewset, 'partial_update'):
            methods.append('PUT')
            methods.append('PATCH')
        if hasattr(viewset, 'destroy'):
            methods.append('DELETE')
    else:
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    return methods

def get_sample_body(viewset, app_name):
    """Generate sample request body based on serializer"""
    body = {}
    
    # App-specific sample data
    samples = {
        'ar': {
            'invoices': {
                "customer": 1,
                "invoice_number": "AR-2024-001",
                "invoice_date": "2024-11-17",
                "due_date": "2024-12-17",
                "currency": "USD",
                "exchange_rate": "1.00",
                "subtotal": "1000.00",
                "tax_amount": "150.00",
                "total": "1150.00",
                "lines": []
            },
            'payments': {
                "customer": 1,
                "payment_number": "PAY-AR-001",
                "payment_date": "2024-11-17",
                "payment_method": "BANK_TRANSFER",
                "currency": "USD",
                "amount": "1000.00",
                "reference": "REF123"
            }
        },
        'ap': {
            'invoices': {
                "supplier": 1,
                "invoice_number": "AP-2024-001",
                "invoice_date": "2024-11-17",
                "due_date": "2024-12-17",
                "currency": "USD",
                "exchange_rate": "1.00",
                "subtotal": "1000.00",
                "tax_amount": "150.00",
                "total": "1150.00"
            },
            'payments': {
                "supplier": 1,
                "payment_number": "PAY-AP-001",
                "payment_date": "2024-11-17",
                "payment_method": "BANK_TRANSFER",
                "currency": "USD",
                "amount": "1000.00",
                "reference": "REF123"
            },
            'vendors': {
                "code": "VEND001",
                "name": "Vendor Name",
                "email": "vendor@example.com",
                "phone": "+1234567890",
                "currency": "USD",
                "payment_terms": "NET30"
            }
        },
        'finance': {
            'journals': {
                "journal_date": "2024-11-17",
                "period": 1,
                "description": "Manual Journal Entry",
                "lines": []
            },
            'currencies': {
                "code": "EUR",
                "name": "Euro",
                "symbol": "€",
                "is_active": True
            },
            'accounts': {
                "code": "1000",
                "alias": "Cash Account",
                "account_type": "ASSET",
                "is_active": True
            }
        },
        'inventory': {
            'balances': {},
            'movements': {},
            'adjustments': {
                "adjustment_date": "2024-11-17",
                "warehouse": 1,
                "reason": "Physical count adjustment",
                "lines": []
            },
            'transfers': {
                "transfer_date": "2024-11-17",
                "from_warehouse": 1,
                "to_warehouse": 2,
                "lines": []
            }
        },
        'procurement': {
            'items': {
                "code": "ITEM001",
                "description": "Product Description",
                "unit_of_measure": "EA",
                "is_active": True
            },
            'purchase-requisitions': {
                "pr_number": "PR-2024-001",
                "requested_date": "2024-11-17",
                "required_date": "2024-12-01",
                "department": "IT",
                "lines": []
            },
            'purchase-orders': {
                "po_number": "PO-2024-001",
                "supplier": 1,
                "order_date": "2024-11-17",
                "delivery_date": "2024-12-01",
                "currency": "USD",
                "lines": []
            }
        },
        'segment': {
            'types': {
                "segment_type": "DEPARTMENT",
                "segment_name": "Department",
                "is_active": True,
                "is_required": True
            },
            'values': {
                "code": "DEPT01",
                "alias": "Sales Department",
                "segment_type": 1,
                "is_active": True
            }
        },
        'periods': {
            'fiscal-years': {
                "year": 2024,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "is_closed": False
            },
            'fiscal-periods': {
                "period_number": 1,
                "period_name": "January 2024",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "fiscal_year": 1
            }
        },
        'crm': {
            'leads': {
                "name": "John Doe",
                "company": "ABC Corp",
                "email": "john@abc.com",
                "phone": "+1234567890",
                "status": "NEW"
            },
            'opportunities': {
                "name": "Software License Deal",
                "customer": 1,
                "amount": "50000.00",
                "probability": 75,
                "stage": "PROPOSAL"
            },
            'contacts': {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "phone": "+1234567890"
            }
        },
        'fixed-assets': {
            'assets': {
                "asset_number": "FA-001",
                "description": "Laptop Computer",
                "category": 1,
                "acquisition_date": "2024-11-17",
                "cost": "2000.00",
                "salvage_value": "200.00",
                "useful_life": 36
            }
        }
    }
    
    # Get sample for this app and endpoint
    for key, value in samples.items():
        if key in app_name.lower():
            return value
    
    return {}

print("Analyzing all API endpoints...")

resolver = get_resolver()
all_urls = get_all_urls(resolver.url_patterns)

# Filter API endpoints
api_urls = [u for u in all_urls if u['path'].startswith('api/')]
print(f"Found {len(api_urls)} total API endpoints")

# Group by app
apps = defaultdict(list)
for url_info in api_urls:
    path = url_info['path']
    # Determine app from path
    parts = path.split('/')
    if len(parts) > 1:
        app_name = parts[1]
        # Further categorize
        if len(parts) > 2 and parts[2] not in ['', ':']:
            subapp = parts[2]
            apps[f"{app_name}/{subapp}"].append(url_info)
        else:
            apps[app_name].append(url_info)

print(f"\nGrouped into {len(apps)} categories:")
for app, endpoints in sorted(apps.items()):
    print(f"  {app}: {len(endpoints)} endpoints")

print("\nGenerating Postman collections...")
print("="*80)

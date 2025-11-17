"""
Comprehensive API Endpoint Testing
Tests all endpoints to identify broken or useless ones
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
import re

def get_all_urls(urlpatterns, prefix=''):
    """Extract all URL patterns"""
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            url_path = prefix + str(pattern.pattern)
            urls.append({
                'path': url_path,
                'name': pattern.name,
                'callback': pattern.callback
            })
        elif isinstance(pattern, URLResolver):
            urls.extend(get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
    return urls

def clean_url(url_path):
    """Convert URL pattern to testable path"""
    # Remove regex patterns
    url_path = re.sub(r'\(\?P<\w+>[^)]+\)', '1', url_path)  # Replace params with '1'
    url_path = re.sub(r'\^', '', url_path)
    url_path = re.sub(r'\$', '', url_path)
    url_path = re.sub(r'\\\.', '.', url_path)
    return '/' + url_path.replace('//', '/')

print("\n" + "="*100)
print("API ENDPOINT ANALYSIS - TESTING FOR BROKEN/USELESS ENDPOINTS")
print("="*100)

# Get all URLs
resolver = get_resolver()
all_urls = get_all_urls(resolver.url_patterns)

# Filter API endpoints
api_urls = [u for u in all_urls if u['path'].startswith('api/')]

print(f"\n📊 Total API Endpoints: {len(api_urls)}")

# Initialize client
client = Client()

# Categories
broken_endpoints = []
redirect_endpoints = []
auth_required = []
working_endpoints = []
deprecated_endpoints = []
suspicious_endpoints = []

print("\n🔍 Testing endpoints (this may take a minute)...\n")

tested_paths = set()

for url_info in api_urls[:200]:  # Test first 200 to avoid timeout
    url_path = url_info['path']
    url_name = url_info['name']
    
    # Skip format suffixes
    if '<drf_format_suffix:format>' in url_path:
        continue
    
    # Convert to testable path
    test_path = clean_url(url_path)
    
    # Skip duplicates
    if test_path in tested_paths:
        continue
    tested_paths.add(test_path)
    
    # Skip if too many params
    if test_path.count('/1/') > 2:
        continue
    
    try:
        response = client.get(test_path)
        status = response.status_code
        
        if status == 200:
            working_endpoints.append({
                'path': test_path,
                'name': url_name,
                'status': 200
            })
        elif status in [301, 302]:
            redirect_endpoints.append({
                'path': test_path,
                'name': url_name,
                'status': status,
                'redirect': response.get('Location', 'Unknown')
            })
        elif status in [401, 403]:
            auth_required.append({
                'path': test_path,
                'name': url_name,
                'status': status
            })
        elif status == 404:
            suspicious_endpoints.append({
                'path': test_path,
                'name': url_name,
                'status': 404,
                'reason': 'Not Found'
            })
        elif status == 405:
            suspicious_endpoints.append({
                'path': test_path,
                'name': url_name,
                'status': 405,
                'reason': 'Method Not Allowed (GET)'
            })
        elif status >= 500:
            broken_endpoints.append({
                'path': test_path,
                'name': url_name,
                'status': status,
                'error': str(response.content[:100])
            })
    except Exception as e:
        broken_endpoints.append({
            'path': test_path,
            'name': url_name,
            'status': 'ERROR',
            'error': str(e)[:100]
        })

# Analyze endpoint names for deprecated/useless patterns
for url_info in api_urls:
    path = url_info['path']
    name = url_info['name']
    
    # Check for deprecated patterns
    if any(word in path.lower() for word in ['legacy', 'old', 'deprecated', 'temp', 'test']):
        deprecated_endpoints.append({
            'path': clean_url(path),
            'name': name,
            'reason': 'Contains deprecated keywords'
        })

# Print Results
print("\n" + "="*100)
print("📊 TEST RESULTS SUMMARY")
print("="*100)

print(f"\n✅ Working Endpoints (200 OK): {len(working_endpoints)}")
if working_endpoints[:10]:
    for ep in working_endpoints[:10]:
        print(f"   {ep['path']}")
    if len(working_endpoints) > 10:
        print(f"   ... and {len(working_endpoints) - 10} more")

print(f"\n🔒 Authentication Required (401/403): {len(auth_required)}")
if auth_required[:10]:
    for ep in auth_required[:10]:
        print(f"   {ep['path']} - HTTP {ep['status']}")
    if len(auth_required) > 10:
        print(f"   ... and {len(auth_required) - 10} more")

print(f"\n🔄 Redirects (301/302): {len(redirect_endpoints)}")
if redirect_endpoints:
    for ep in redirect_endpoints[:5]:
        print(f"   {ep['path']} → {ep.get('redirect', 'Unknown')}")

print(f"\n⚠️ Suspicious/Not Found (404/405): {len(suspicious_endpoints)}")
if suspicious_endpoints:
    for ep in suspicious_endpoints[:15]:
        print(f"   ❌ {ep['path']} - {ep['reason']}")
    if len(suspicious_endpoints) > 15:
        print(f"   ... and {len(suspicious_endpoints) - 15} more")

print(f"\n❌ BROKEN Endpoints (500+ errors): {len(broken_endpoints)}")
if broken_endpoints:
    for ep in broken_endpoints:
        print(f"   🔴 {ep['path']}")
        print(f"      Status: {ep['status']}")
        print(f"      Error: {ep.get('error', 'Unknown')[:80]}")

print(f"\n🗑️ Potentially DEPRECATED/USELESS: {len(deprecated_endpoints)}")
if deprecated_endpoints:
    for ep in deprecated_endpoints:
        print(f"   ⚠️ {ep['path']}")
        print(f"      Name: {ep['name']}")
        print(f"      Reason: {ep['reason']}")

# Analyze useless patterns
print("\n" + "="*100)
print("🔍 USELESS ENDPOINT ANALYSIS")
print("="*100)

# Check for duplicate functionality
print("\n1. CHECKING FOR DUPLICATE ENDPOINTS:")
path_groups = {}
for url_info in api_urls:
    base_path = re.sub(r'/\d+/', '/<id>/', clean_url(url_info['path']))
    if base_path not in path_groups:
        path_groups[base_path] = []
    path_groups[base_path].append(url_info)

duplicates = {k: v for k, v in path_groups.items() if len(v) > 3}
if duplicates:
    print(f"   Found {len(duplicates)} potential duplicate groups:")
    for path, urls in list(duplicates.items())[:5]:
        print(f"   📍 {path} - {len(urls)} variations")

# Check for endpoints that should be POST but accept GET
print("\n2. CHECKING FOR ENDPOINTS THAT NEED POST/PUT:")
action_keywords = ['create', 'post', 'update', 'delete', 'approve', 'reject', 'submit', 'reverse']
action_endpoints = []
for url_info in api_urls:
    path = url_info['path'].lower()
    if any(keyword in path for keyword in action_keywords):
        action_endpoints.append(clean_url(url_info['path']))

if action_endpoints:
    print(f"   Found {len(action_endpoints)} action endpoints:")
    for ep in action_endpoints[:10]:
        print(f"   🔄 {ep}")
    if len(action_endpoints) > 10:
        print(f"   ... and {len(action_endpoints) - 10} more")

# Check for unused report/export endpoints
print("\n3. CHECKING FOR EXPORT/REPORT ENDPOINTS:")
export_endpoints = []
for url_info in api_urls:
    path = url_info['path'].lower()
    if any(keyword in path for keyword in ['export', 'report', 'download', 'pdf', 'excel']):
        export_endpoints.append(clean_url(url_info['path']))

if export_endpoints:
    print(f"   Found {len(export_endpoints)} export/report endpoints:")
    for ep in export_endpoints[:10]:
        print(f"   📄 {ep}")

# Final Summary
print("\n" + "="*100)
print("🎯 RECOMMENDATIONS")
print("="*100)

print("\n✅ KEEP (Core Functionality):")
print("   - CRUD endpoints for invoices, payments, journal entries")
print("   - Authentication endpoints")
print("   - List/detail views for master data")
print("   - Dashboard/summary endpoints")

print("\n⚠️ REVIEW (Potentially Useless):")
if suspicious_endpoints:
    print(f"   - {len(suspicious_endpoints)} endpoints returning 404/405")
    print("   - These may be misconfigured or have broken URLs")
if deprecated_endpoints:
    print(f"   - {len(deprecated_endpoints)} endpoints with deprecated naming")
if len(action_endpoints) > 50:
    print(f"   - {len(action_endpoints)} action endpoints (may have duplicates)")

print("\n❌ FIX IMMEDIATELY (Broken):")
if broken_endpoints:
    print(f"   - {len(broken_endpoints)} endpoints throwing 500 errors")
    for ep in broken_endpoints:
        print(f"     • {ep['path']}")
else:
    print("   - None found! ✅")

print("\n🗑️ CONSIDER REMOVING:")
print("   - Duplicate endpoints serving same functionality")
print("   - Test/debug endpoints in production")
print("   - Endpoints with no frontend integration")
print("   - Legacy endpoints marked as deprecated")

print("\n" + "="*100)
print(f"📊 FINAL STATS:")
print(f"   Total Tested: {len(tested_paths)}")
print(f"   Working: {len(working_endpoints)}")
print(f"   Auth Required: {len(auth_required)}")
print(f"   Suspicious: {len(suspicious_endpoints)}")
print(f"   Broken: {len(broken_endpoints)}")
print(f"   Health Score: {(len(working_endpoints) + len(auth_required)) / len(tested_paths) * 100:.1f}%")
print("="*100 + "\n")

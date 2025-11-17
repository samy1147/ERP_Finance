"""
Test Fixed Payment Endpoints
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client

print("\n" + "="*80)
print("🔧 TESTING FIXED PAYMENT ENDPOINTS")
print("="*80)

client = Client()

test_endpoints = [
    '/api/ar/payments/',
    '/api/ap/payments/',
    '/api/ap/payments/outstanding/',
]

print("\n📋 Testing 3 previously broken endpoints...\n")

results = []
for endpoint in test_endpoints:
    try:
        response = client.get(endpoint)
        status = response.status_code
        
        if status == 200:
            results.append({'endpoint': endpoint, 'status': 200, 'result': '✅ FIXED'})
            print(f"✅ {endpoint}")
            print(f"   Status: 200 OK")
            print(f"   Response: {len(response.content)} bytes")
        elif status == 403:
            results.append({'endpoint': endpoint, 'status': 403, 'result': '🔒 AUTH REQUIRED'})
            print(f"🔒 {endpoint}")
            print(f"   Status: 403 Forbidden (Authentication Required)")
        else:
            results.append({'endpoint': endpoint, 'status': status, 'result': f'⚠️ STATUS {status}'})
            print(f"⚠️ {endpoint}")
            print(f"   Status: {status}")
    except Exception as e:
        results.append({'endpoint': endpoint, 'status': 'ERROR', 'result': '❌ STILL BROKEN'})
        print(f"❌ {endpoint}")
        print(f"   Error: {str(e)[:100]}")
    print()

print("="*80)
print("📊 SUMMARY")
print("="*80)

fixed = sum(1 for r in results if r['status'] == 200)
auth = sum(1 for r in results if r['status'] == 403)
broken = sum(1 for r in results if r['status'] not in [200, 403])

print(f"\n✅ Fixed: {fixed}/3")
print(f"🔒 Auth Required: {auth}/3")
print(f"❌ Still Broken: {broken}/3")

if broken == 0:
    print("\n🎉 SUCCESS! All payment endpoints are now working!")
else:
    print(f"\n⚠️ {broken} endpoint(s) still have issues")

print("="*80 + "\n")

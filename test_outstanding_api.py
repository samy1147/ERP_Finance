"""
Test the outstanding invoices API endpoint
"""
import requests

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTING OUTSTANDING INVOICES API")
print("=" * 70)

# Test with customer ID 3 (Deutsche Handel GmbH - Germany)
customer_id = 3

print(f"\nTesting: GET {BASE_URL}/api/outstanding-invoices/?customer={customer_id}")
print("-" * 70)

try:
    response = requests.get(
        f"{BASE_URL}/api/outstanding-invoices/",
        params={"customer": customer_id},
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(response.text)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nParsed Data:")
        print(f"Type: {type(data)}")
        print(f"Number of invoices: {len(data) if isinstance(data, list) else 'N/A'}")
        
        if isinstance(data, list) and len(data) > 0:
            print("\nInvoice Details:")
            for idx, inv in enumerate(data, 1):
                print(f"\n  Invoice {idx}:")
                print(f"    ID: {inv.get('id')}")
                print(f"    Number: {inv.get('number')}")
                print(f"    Date: {inv.get('date')}")
                print(f"    Total: ${inv.get('total', 0):.2f}")
                print(f"    Paid: ${inv.get('paid', 0):.2f}")
                print(f"    Outstanding: ${inv.get('outstanding', 0):.2f}")
                print(f"    Currency: {inv.get('currency')}")
        else:
            print("\n❌ No invoices returned (empty array)")
    else:
        print(f"\n❌ Error: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to backend server")
    print("   Make sure Django is running on http://localhost:8000")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 70)

"""
Test the AP outstanding invoices API endpoint
"""
import requests

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTING AP OUTSTANDING INVOICES API")
print("=" * 70)

# Test with supplier ID 9 (Italia Machinery SRL - Milan)
supplier_id = 9

print(f"\nTesting: GET {BASE_URL}/api/outstanding-invoices/?supplier={supplier_id}")
print("-" * 70)

try:
    response = requests.get(
        f"{BASE_URL}/api/outstanding-invoices/",
        params={"supplier": supplier_id},
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Body:")
    print(response.text)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nParsed Data:")
        print(f"Type: {type(data)}")
        print(f"Number of invoices: {len(data) if isinstance(data, list) else 'N/A'}")
        
        if isinstance(data, list) and len(data) > 0:
            print("\n✅ SUCCESS! Invoices returned:")
            for idx, inv in enumerate(data, 1):
                print(f"\n  Invoice {idx}:")
                print(f"    ID: {inv.get('id')}")
                print(f"    Number: {inv.get('number')}")
                print(f"    Date: {inv.get('date')}")
                print(f"    Due Date: {inv.get('due_date')}")
                print(f"    Total: ${inv.get('total', 0):.2f}")
                print(f"    Paid: ${inv.get('paid', 0):.2f}")
                print(f"    Outstanding: ${inv.get('outstanding', 0):.2f}")
                print(f"    Currency: {inv.get('currency')}")
        elif isinstance(data, list):
            print("\n❌ PROBLEM: Empty array returned (no invoices)")
            print("   This means backend found no outstanding invoices")
        else:
            print(f"\n❌ PROBLEM: Unexpected response format: {type(data)}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to backend server")
    print("   Make sure Django is running on http://localhost:8000")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nExpected Response Format:")
print('''
[
  {
    "id": 1,
    "number": "1",
    "date": "2025-10-17",
    "due_date": "2025-11-17",
    "total": 1050.0,
    "paid": 0.0,
    "outstanding": 1050.0,
    "currency": "EUR"
  }
]
''')
print("\nFrontend should map:")
print("  - inv.number → invoiceNumber")
print("  - inv.outstanding → outstanding")
print("  - NOT inv.invoice_number or inv.outstanding_amount")

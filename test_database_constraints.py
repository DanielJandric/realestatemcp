"""
Test database constraints and verify data quality
"""
import requests
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def test_constraint(description, table, data, should_fail=True):
    """Test a database constraint"""
    print(f"\n  Testing: {description}")
    
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = requests.post(url, headers=HEADERS, json=data)
    
    if should_fail:
        if response.status_code not in [200, 201]:
            print(f"    ✅ PASS - Constraint blocked invalid data (status {response.status_code})")
            return True
        else:
            print(f"    ❌ FAIL - Invalid data was accepted!")
            return False
    else:
        if response.status_code in [200, 201]:
            print(f"    ✅ PASS - Valid data accepted")
            # Clean up
            if response.json():
                item_id = response.json()[0]['id']
                requests.delete(f"{url}?id=eq.{item_id}", headers=HEADERS)
            return True
        else:
            print(f"    ❌ FAIL - Valid data was rejected! {response.text}")
            return False

def test_property_constraints():
    print("\n" + "="*70)
    print("  PROPERTY CONSTRAINTS")
    print("="*70)
    
    results = []
    
    # Test empty name
    results.append(test_constraint(
        "Empty property name should be rejected",
        "properties",
        {"name": "", "city": "Test"},
        should_fail=True
    ))
    
    # Test valid property
    results.append(test_constraint(
        "Valid property should be accepted",
        "properties",
        {"name": "Test Property", "city": "Test City"},
        should_fail=False
    ))
    
    return all(results)

def test_unit_constraints():
    print("\n" + "="*70)
    print("  UNIT CONSTRAINTS")
    print("="*70)
    
    results = []
    
    # Get a property ID first
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/properties?select=id&limit=1", headers=HEADERS)
    if resp.status_code == 200 and resp.json():
        prop_id = resp.json()[0]['id']
        
        # Test negative surface area
        results.append(test_constraint(
            "Negative surface area should be rejected",
            "units",
            {"property_id": prop_id, "surface_area": -50},
            should_fail=True
        ))
        
        # Test negative rooms
        results.append(test_constraint(
            "Negative rooms should be rejected",
            "units",
            {"property_id": prop_id, "rooms": -2},
            should_fail=True
        ))
        
        # Test valid unit
        results.append(test_constraint(
            "Valid unit should be accepted",
            "units",
            {"property_id": prop_id, "unit_number": "TEST-001", "surface_area": 50, "rooms": 2},
            should_fail=False
        ))
    else:
        print("  ⚠️  No properties found for testing")
        return False
    
    return all(results)

def test_tenant_constraints():
    print("\n" + "="*70)
    print("  TENANT CONSTRAINTS")
    print("="*70)
    
    results = []
    
    # Test empty name
    results.append(test_constraint(
        "Empty tenant name should be rejected",
        "tenants",
        {"name": ""},
        should_fail=True
    ))
    
    # Test invalid email
    results.append(test_constraint(
        "Invalid email format should be rejected",
        "tenants",
        {"name": "Test Tenant", "email": "not-an-email"},
        should_fail=True
    ))
    
    # Test valid tenant
    results.append(test_constraint(
        "Valid tenant should be accepted",
        "tenants",
        {"name": "Test Tenant", "email": "test@example.com"},
        should_fail=False
    ))
    
    return all(results)

def test_lease_constraints():
    print("\n" + "="*70)
    print("  LEASE CONSTRAINTS")
    print("="*70)
    
    results = []
    
    # Get unit and tenant IDs
    unit_resp = requests.get(f"{SUPABASE_URL}/rest/v1/units?select=id&limit=1", headers=HEADERS)
    tenant_resp = requests.get(f"{SUPABASE_URL}/rest/v1/tenants?select=id&limit=1", headers=HEADERS)
    
    if unit_resp.status_code == 200 and unit_resp.json() and tenant_resp.status_code == 200 and tenant_resp.json():
        unit_id = unit_resp.json()[0]['id']
        tenant_id = tenant_resp.json()[0]['id']
        
        # Test negative rent
        results.append(test_constraint(
            "Negative rent should be rejected",
            "leases",
            {"unit_id": unit_id, "tenant_id": tenant_id, "rent_net": -1000},
            should_fail=True
        ))
        
        # Test negative charges
        results.append(test_constraint(
            "Negative charges should be rejected",
            "leases",
            {"unit_id": unit_id, "tenant_id": tenant_id, "charges": -100},
            should_fail=True
        ))
        
        # Test invalid date range
        results.append(test_constraint(
            "End date before start date should be rejected",
            "leases",
            {"unit_id": unit_id, "tenant_id": tenant_id, "start_date": "2024-12-31", "end_date": "2024-01-01"},
            should_fail=True
        ))
        
        # Test invalid status
        results.append(test_constraint(
            "Invalid status should be rejected",
            "leases",
            {"unit_id": unit_id, "tenant_id": tenant_id, "status": "invalid_status"},
            should_fail=True
        ))
        
        # Test valid lease
        results.append(test_constraint(
            "Valid lease should be accepted",
            "leases",
            {"unit_id": unit_id, "tenant_id": tenant_id, "rent_net": 1500, "charges": 200, 
             "start_date": "2024-01-01", "end_date": "2024-12-31", "status": "active"},
            should_fail=False
        ))
    else:
        print("  ⚠️  Required data not found for testing")
        return False
    
    return all(results)

def test_dispute_constraints():
    print("\n" + "="*70)
    print("  DISPUTE CONSTRAINTS")
    print("="*70)
    
    results = []
    
    # Get property ID
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/properties?select=id&limit=1", headers=HEADERS)
    if resp.status_code == 200 and resp.json():
        prop_id = resp.json()[0]['id']
        
        # Test negative amount
        results.append(test_constraint(
            "Negative dispute amount should be rejected",
            "disputes",
            {"property_id": prop_id, "amount": -500},
            should_fail=True
        ))
        
        # Test valid dispute
        results.append(test_constraint(
            "Valid dispute should be accepted",
            "disputes",
            {"property_id": prop_id, "description": "Test dispute", "amount": 500, "status": "open"},
            should_fail=False
        ))
    else:
        print("  ⚠️  No properties found for testing")
        return False
    
    return all(results)

def test_maintenance_constraints():
    print("\n" + "="*70)
    print("  MAINTENANCE CONSTRAINTS")
    print("="*70)
    
    results = []
    
    # Get property ID
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/properties?select=id&limit=1", headers=HEADERS)
    if resp.status_code == 200 and resp.json():
        prop_id = resp.json()[0]['id']
        
        # Test negative cost
        results.append(test_constraint(
            "Negative maintenance cost should be rejected",
            "maintenance",
            {"property_id": prop_id, "cost": -1000},
            should_fail=True
        ))
        
        # Test invalid date range
        results.append(test_constraint(
            "End date before start date should be rejected",
            "maintenance",
            {"property_id": prop_id, "start_date": "2024-12-31", "end_date": "2024-01-01"},
            should_fail=True
        ))
        
        # Test valid maintenance
        results.append(test_constraint(
            "Valid maintenance contract should be accepted",
            "maintenance",
            {"property_id": prop_id, "provider": "Test Provider", "cost": 1000, 
             "start_date": "2024-01-01", "end_date": "2024-12-31"},
            should_fail=False
        ))
    else:
        print("  ⚠️  No properties found for testing")
        return False
    
    return all(results)

def main():
    print("\n" + "="*70)
    print("  🛡️  DATABASE CONSTRAINTS TEST SUITE")
    print("="*70)
    print("\n  Testing CHECK constraints and data validation...")
    
    results = {
        "Properties": test_property_constraints(),
        "Units": test_unit_constraints(),
        "Tenants": test_tenant_constraints(),
        "Leases": test_lease_constraints(),
        "Disputes": test_dispute_constraints(),
        "Maintenance": test_maintenance_constraints()
    }
    
    print("\n" + "="*70)
    print("  TEST RESULTS SUMMARY")
    print("="*70)
    
    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {category}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("  ✅ ALL CONSTRAINT TESTS PASSED!")
        print("  Database constraints are working correctly.")
    else:
        print("  ⚠️  SOME TESTS FAILED")
        print("  Please review the failures above.")
    print("="*70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

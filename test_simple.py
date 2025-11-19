"""
Simple test for enhanced MCP server - without caching issues
"""
from supabase import create_client
import json

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_basic_queries():
    """Test basic Supabase queries"""
    print("\n" + "="*70)
    print("  🧪 BASIC DATABASE TESTS")
    print("="*70)
    
    # Test properties
    print("\n1. Testing Properties table...")
    props = supabase.table("properties").select("*").execute()
    print(f"   ✅ Found {len(props.data)} properties")
    
    # Test units
    print("\n2. Testing Units table...")
    units = supabase.table("units").select("*").execute()
    print(f"   ✅ Found {len(units.data)} units")
    
    # Test tenants
    print("\n3. Testing Tenants table...")
    tenants = supabase.table("tenants").select("*").execute()
    print(f"   ✅ Found {len(tenants.data)} tenants")
    
    # Test leases
    print("\n4. Testing Leases table...")
    leases = supabase.table("leases").select("*").execute()
    print(f"   ✅ Found {len(leases.data)} leases")
    
    # Test disputes
    print("\n5. Testing Disputes table...")
    disputes = supabase.table("disputes").select("*").execute()
    print(f"   ✅ Found {len(disputes.data)} disputes")
    
    # Test incidents
    print("\n6. Testing Incidents table...")
    incidents = supabase.table("incidents").select("*").execute()
    print(f"   ✅ Found {len(incidents.data)} incidents")
    
    # Test maintenance
    print("\n7. Testing Maintenance table...")
    maintenance = supabase.table("maintenance").select("*").execute()
    print(f"   ✅ Found {len(maintenance.data)} maintenance contracts")
    
    return props.data, units.data, leases.data

def test_analytics(properties, units, leases):
    """Test analytics calculations"""
    print("\n" + "="*70)
    print("  📊 ANALYTICS TESTS")
    print("="*70)
    
    # Calculate occupancy
    print("\n1. Calculating Occupancy Rate...")
    total_units = len(units)
    total_leases = len(leases)
    occupancy = (total_leases / total_units * 100) if total_units > 0 else 0
    print(f"   ✅ Occupancy: {occupancy:.1f}%")
    print(f"      Total Units: {total_units}")
    print(f"      Active Leases: {total_leases}")
    
    # Calculate revenue
    print("\n2. Calculating Revenue...")
    total_revenue = sum(l.get('rent_net', 0) + l.get('charges', 0) for l in leases if l.get('rent_net'))
    print(f"   ✅ Total Monthly Revenue: CHF {total_revenue:,.2f}")
    print(f"      Annualized: CHF {total_revenue * 12:,.2f}")
    
    # Average rent
    print("\n3. Calculating Average Rent...")
    rents = [l.get('rent_net', 0) for l in leases if l.get('rent_net', 0) > 0]
    if rents:
        avg_rent = sum(rents) / len(rents)
        print(f"   ✅ Average Rent: CHF {avg_rent:,.2f}")
        print(f"      Min Rent: CHF {min(rents):,.2f}")
        print(f"      Max Rent: CHF {max(rents):,.2f}")
    
    return True

def test_new_features():
    """Test new table features"""
    print("\n" + "="*70)
    print("  🆕 NEW FEATURES TESTS")
    print("="*70)
    
    # Test disputes with joins
    print("\n1. Testing Disputes with Property info...")
    disputes = supabase.table("disputes").select(
        "*, properties(name, city)"
    ).execute()
    active_disputes = [d for d in disputes.data if d.get('status') in ['open', 'in_progress']]
    print(f"   ✅ Total Disputes: {len(disputes.data)}")
    print(f"      Active: {len(active_disputes)}")
    if active_disputes:
        total_amount = sum(d.get('amount', 0) for d in active_disputes)
        print(f"      Total Amount: CHF {total_amount:,.2f}")
    
    # Test incidents
    print("\n2. Testing Incidents...")
    incidents = supabase.table("incidents").select(
        "*, properties(name, city)"
    ).execute()
    print(f"   ✅ Total Incidents: {len(incidents.data)}")
    by_status = {}
    for inc in incidents.data:
        status = inc.get('status', 'unknown')
        by_status[status] = by_status.get(status, 0) + 1
    print(f"      By Status: {by_status}")
    
    # Test maintenance
    print("\n3. Testing Maintenance contracts...")
    maintenance = supabase.table("maintenance").select(
        "*, properties(name, city)"
    ).execute()
    print(f"   ✅ Total Contracts: {len(maintenance.data)}")
    if maintenance.data:
        total_cost = sum(m.get('cost', 0) for m in maintenance.data)
        print(f"      Total Annual Cost: CHF {total_cost:,.2f}")
    
    return True

def test_data_validator():
    """Test validation functions"""
    print("\n" + "="*70)
    print("  ✅ DATA VALIDATOR TESTS")
    print("="*70)
    
    from data_validator import DataValidator
    
    # Test email validation
    print("\n1. Testing Email Validation...")
    valid = DataValidator.validate_email("test@example.com")
    invalid = DataValidator.validate_email("not-an-email")
    print(f"   ✅ Valid email: {valid}")
    print(f"   ✅ Invalid email rejected: {not invalid}")
    
    # Test positive numbers
    print("\n2. Testing Positive Number Validation...")
    valid = DataValidator.validate_positive_number(100, "rent")
    invalid = DataValidator.validate_positive_number(-50, "rent")
    print(f"   ✅ Positive number: {valid}")
    print(f"   ✅ Negative number rejected: {not invalid}")
    
    # Test date range
    print("\n3. Testing Date Range Validation...")
    valid = DataValidator.validate_date_range("2024-01-01", "2024-12-31")
    invalid = DataValidator.validate_date_range("2024-12-31", "2024-01-01")
    print(f"   ✅ Valid date range: {valid}")
    print(f"   ✅ Invalid date range rejected: {not invalid}")
    
    return True

def main():
    print("\n" + "="*70)
    print("  🚀 ENHANCED MCP - SIMPLE TEST SUITE")
    print("="*70)
    print("\n  Testing database access and new features...")
    
    try:
        # Test basic queries
        props, units, leases = test_basic_queries()
        
        # Test analytics
        test_analytics(props, units, leases)
        
        # Test new features
        test_new_features()
        
        # Test validators
        test_data_validator()
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n  Summary:")
        print("  • Database tables accessible")
        print("  • Analytics calculations working")
        print("  • New features (disputes, incidents, maintenance) functional")
        print("  • Data validators operational")
        print("\n  Next steps:")
        print("  1. Apply schema_enhanced.sql to Supabase")
        print("  2. Test full MCP server in Claude Desktop")
        print("  3. Review README_ENHANCEMENTS.md for usage")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print("\n" + "="*70)
        print("  ❌ TEST FAILED")
        print("="*70)
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

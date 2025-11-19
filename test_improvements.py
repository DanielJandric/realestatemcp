"""
Test the new schema improvements
"""
from supabase import create_client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*70)
print("  TESTING SCHEMA IMPROVEMENTS")
print("="*70)

# Get Place Centrale 3 ID
place_centrale_id = "52990a0c-bd0c-40be-b83b-4bc1bc9777e6"

print("\n📊 Testing new utility functions...")

# Test 1: Vacancy rate
try:
    print("\n1. get_vacancy_rate (Place Centrale 3):")
    res = supabase.rpc('get_vacancy_rate', {'p_property_id': place_centrale_id}).execute()
    print(f"   ✅ Vacancy rate: {res.data}%")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Projected revenue
try:
    print("\n2. project_annual_revenue (Place Centrale 3):")
    res = supabase.rpc('project_annual_revenue', {'p_property_id': place_centrale_id}).execute()
    print(f"   ✅ Annual revenue: CHF {res.data:,.2f}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Expiring leases
try:
    print("\n3. get_expiring_leases (next 6 months):")
    res = supabase.rpc('get_expiring_leases', {'months_ahead': 6}).execute()
    print(f"   ✅ Found {len(res.data)} leases expiring")
    if res.data:
        print(f"   First: {res.data[0].get('tenant_name')} - {res.data[0].get('end_date')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Average rent per sqm
try:
    print("\n4. get_avg_rent_per_sqm (Place Centrale 3):")
    res = supabase.rpc('get_avg_rent_per_sqm', {'p_property_id': place_centrale_id}).execute()
    print(f"   ✅ Avg rent/m²: CHF {res.data:.2f}" if res.data else "   ✅ No data (expected for units without area)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Check new tables exist
print("\n📋 Checking new tables...")
new_tables = ['rent_history', 'rent_payments', 'inspections', 'charge_details', 
              'lease_renewals', 'communications']

for table in new_tables:
    try:
        res = supabase.table(table).select("*", count="exact").limit(1).execute()
        print(f"   ✅ {table}: exists ({res.count or 0} records)")
    except Exception as e:
        print(f"   ❌ {table}: {str(e)[:50]}")

# Test 6: Check materialized views
print("\n📊 Checking materialized views...")
try:
    query = """
    SELECT matviewname 
    FROM pg_matviews 
    WHERE schemaname = 'public' 
    AND matviewname LIKE 'mv_%'
    """
    res = supabase.rpc("exec_sql", {"query": query}).execute()
    if res.data:
        print(f"   ✅ Found {len(res.data)} materialized views:")
        for view in res.data:
            print(f"      - {view['matviewname']}")
except Exception as e:
    print(f"   ❌ Error: {str(e)[:100]}")

# Test 7: Check constraints
print("\n🔒 Checking integrity constraints...")
try:
    query = """
    SELECT conname, contype 
    FROM pg_constraint 
    WHERE conrelid = 'leases'::regclass 
    AND conname IN ('no_lease_overlap', 'rent_non_negative')
    """
    res = supabase.rpc("exec_sql", {"query": query}).execute()
    if res.data:
        print(f"   ✅ Found {len(res.data)} constraints on leases:")
        for c in res.data:
            print(f"      - {c['conname']} ({c['contype']})")
except Exception as e:
    print(f"   ⚠️  {str(e)[:100]}")

print("\n" + "="*70)
print("  ✅ TESTING COMPLETE")
print("="*70)
print("\n💡 To refresh materialized views, run in Supabase SQL Editor:")
print("   SELECT refresh_all_materialized_views();")



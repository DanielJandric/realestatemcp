"""
Diagnostic script for Place Centrale 3 revenue issue
"""
from supabase import create_client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def diagnose_place_centrale():
    print("\n" + "="*70)
    print("  🔍 DIAGNOSTIC: Place Centrale 3 - Martigny")
    print("="*70)
    
    # 1. Find the property
    print("\n1️⃣ Searching for property...")
    props = supabase.table("properties").select("*").ilike("name", "%Place Centrale%").execute()
    
    if not props.data:
        print("   ❌ Property not found!")
        return
    
    prop = props.data[0]
    print(f"   ✅ Found: {prop['name']} (ID: {prop['id']})")
    print(f"      City: {prop.get('city', 'N/A')}")
    print(f"      Address: {prop.get('address', 'N/A')}")
    
    # 2. Find units
    print("\n2️⃣ Checking units...")
    units = supabase.table("units").select("*").eq("property_id", prop['id']).execute()
    
    print(f"   ✅ Found {len(units.data)} units")
    for i, unit in enumerate(units.data, 1):
        print(f"      {i}. Unit: {unit.get('unit_number', 'N/A')}, Type: {unit.get('type', 'N/A')}, Area: {unit.get('surface_area', 'N/A')} m²")
    
    if not units.data:
        print("   ⚠️  No units found for this property!")
        return
    
    # 3. Find leases
    print("\n3️⃣ Checking leases...")
    unit_ids = [u['id'] for u in units.data]
    
    leases = supabase.table("leases").select(
        "*, tenants(name), units(unit_number)"
    ).in_("unit_id", unit_ids).execute()
    
    print(f"   Found {len(leases.data)} leases total")
    
    active_leases = [l for l in leases.data if l.get('status') == 'active']
    print(f"   ✅ Active leases: {len(active_leases)}")
    
    # Analyze each lease
    total_revenue = 0
    zero_rent_count = 0
    low_rent_count = 0
    
    print("\n   📊 Lease Details:")
    for i, lease in enumerate(leases.data, 1):
        rent = lease.get('rent_net', 0) or 0
        charges = lease.get('charges', 0) or 0
        status = lease.get('status', 'unknown')
        tenant_name = lease.get('tenants', {}).get('name', 'Unknown') if lease.get('tenants') else 'Unknown'
        unit_num = lease.get('units', {}).get('unit_number', 'N/A') if lease.get('units') else 'N/A'
        
        total = rent + charges
        
        # Categorize
        if rent == 0:
            zero_rent_count += 1
            status_icon = "⚠️"
        elif rent < 100:
            low_rent_count += 1
            status_icon = "⚠️"
        else:
            status_icon = "✅"
        
        if status == 'active':
            total_revenue += total
        
        print(f"      {i}. {status_icon} Unit {unit_num} | Status: {status}")
        print(f"         Tenant: {tenant_name}")
        print(f"         Rent: CHF {rent:.2f} | Charges: CHF {charges:.2f} | Total: CHF {total:.2f}")
    
    # 4. Summary
    print("\n" + "="*70)
    print("  📊 SUMMARY")
    print("="*70)
    print(f"\n  Property: {prop['name']}")
    print(f"  Total Units: {len(units.data)}")
    print(f"  Total Leases: {len(leases.data)}")
    print(f"  Active Leases: {len(active_leases)}")
    print(f"  Total Monthly Revenue (active): CHF {total_revenue:,.2f}")
    
    print(f"\n  ⚠️  Issues Found:")
    print(f"  • Leases with ZERO rent: {zero_rent_count}")
    print(f"  • Leases with LOW rent (<100): {low_rent_count}")
    
    # 5. Detailed problem analysis
    if zero_rent_count > 0 or low_rent_count > 0:
        print("\n" + "="*70)
        print("  🔍 PROBLEM ANALYSIS")
        print("="*70)
        
        print("\n  Probable causes:")
        print("  1. Data import issue - rent values not parsed correctly")
        print("  2. Excel file has missing or corrupted rent data")
        print("  3. Rent values in wrong column during import")
        
        print("\n  📋 Recommended Actions:")
        print("  1. Check the original Excel file:")
        print("     Incremental1/01. Etat locatif/Etat_locatif_ 45635 Pl.Centrale 3 Martigny.xlsx")
        print("  2. Verify rent column mapping in sync_supabase.py")
        print("  3. Re-import data for this property with corrected mapping")
        print("  4. Update existing leases with correct rent values")
    
    # 6. Show original file location
    print("\n" + "="*70)
    print("  📁 SOURCE FILES")
    print("="*70)
    print("\n  Excel file location:")
    print("  c:/OneDriveExport/Incremental1/01. Etat locatif/Etat_locatif_ 45635 Pl.Centrale 3 Martigny.xlsx")
    
    return prop, units.data, leases.data

if __name__ == "__main__":
    try:
        result = diagnose_place_centrale()
        print("\n" + "="*70)
        print("  ✅ Diagnostic Complete")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

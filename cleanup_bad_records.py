from supabase import create_client, Client
import re

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cleanup_bad_records():
    print("=== Quick Fix: Deleting Bad Records ===\n")
    
    # 1. Delete 'nan' unit
    print("Deleting 'nan' unit...")
    nan_units = supabase.table("units").select("id").eq("unit_number", "nan").execute()
    if nan_units.data:
        for unit in nan_units.data:
            # First delete associated leases
            supabase.table("leases").delete().eq("unit_id", unit['id']).execute()
            # Then delete the unit
            supabase.table("units").delete().eq("id", unit['id']).execute()
        print(f"✅ Deleted {len(nan_units.data)} 'nan' unit(s)")
    else:
        print("No 'nan' units found")
    
    # 2. Delete date-like tenant names
    print("\nDeleting date-like tenant names...")
    all_tenants = supabase.table("tenants").select("*").execute()
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    date_tenants = [t for t in all_tenants.data if date_pattern.search(t['name'])]
    
    if date_tenants:
        for tenant in date_tenants:
            print(f"  - Deleting: {tenant['name']}")
            # Delete associated leases first
            supabase.table("leases").delete().eq("tenant_id", tenant['id']).execute()
            # Delete associated documents
            supabase.table("documents").delete().eq("tenant_id", tenant['id']).execute()
            # Delete the tenant
            supabase.table("tenants").delete().eq("id", tenant['id']).execute()
        print(f"✅ Deleted {len(date_tenants)} date-like tenant(s)")
    else:
        print("No date-like tenants found")
    
    print("\n✅ Cleanup complete!")
    print("\nRe-running verification...")
    
    # Quick stats
    props = supabase.table("properties").select("*", count="exact").execute()
    tenants = supabase.table("tenants").select("*", count="exact").execute()
    units = supabase.table("units").select("*", count="exact").execute()
    leases = supabase.table("leases").select("*", count="exact").execute()
    
    print(f"\nFinal counts:")
    print(f"  Properties: {props.count}")
    print(f"  Tenants: {tenants.count}")
    print(f"  Units: {units.count}")
    print(f"  Leases: {leases.count}")

if __name__ == "__main__":
    cleanup_bad_records()

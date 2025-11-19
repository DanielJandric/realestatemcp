from supabase import create_client, Client
import json

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def inspect_martigny():
    print("Searching for 'Martigny'...")
    # Find property matching 'Martigny' or 'Place'
    props = supabase.table("properties").select("*").or_("name.ilike.%Martigny%,name.ilike.%Place%").execute()
    
    print(f"Found {len(props.data)} properties matching 'Martigny' or 'Place'.")
    for p in props.data:
        print(f"Property: {p['name']} (ID: {p['id']})")
        if "Place" in p['name'] or "Martigny" in p['name']:
             print(f"--> POTENTIAL MATCH: {p['name']}")
             inspect_property(p['id'])

def inspect_property(p_id):
    # Get units for property, then leases for those units
    units = supabase.table("units").select("id, unit_number, surface_area, rooms").eq("property_id", p_id).execute()
    print(f"Found {len(units.data)} units.")
    
    unit_ids = [u['id'] for u in units.data]
    
    if unit_ids:
        leases = supabase.table("leases").select(
            "*, tenants(name)"
        ).in_("unit_id", unit_ids).execute()
        
        print(f"Found {len(leases.data)} leases.")
        for l in leases.data:
            tenant_name = l['tenants']['name'] if l['tenants'] else "Unknown"
            unit = next((u for u in units.data if u['id'] == l['unit_id']), None)
            unit_num = unit['unit_number'] if unit else "Unknown"
            print(f"  - Unit: {unit_num}, Tenant: {tenant_name}, Rent: {l['rent_net']}, Start: {l['start_date']}")


if __name__ == "__main__":
    inspect_martigny()

from supabase import create_client, Client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_links():
    print("--- Verifying New Table Relationships ---")
    
    # 1. Disputes
    print("\n[Disputes]")
    # Check how many have property_id
    res = supabase.table("disputes").select("id, property_id, tenant_id, properties(name), tenants(name)").limit(5).execute()
    for item in res.data:
        p_name = item['properties']['name'] if item['properties'] else "UNLINKED"
        t_name = item['tenants']['name'] if item['tenants'] else "UNLINKED"
        print(f"  Dispute {item['id'][:6]} -> Property: {p_name}, Tenant: {t_name}")

    # 2. Incidents
    print("\n[Incidents]")
    res = supabase.table("incidents").select("id, property_id, tenant_id, properties(name), tenants(name)").limit(5).execute()
    for item in res.data:
        p_name = item['properties']['name'] if item['properties'] else "UNLINKED"
        t_name = item['tenants']['name'] if item['tenants'] else "UNLINKED"
        print(f"  Incident {item['id'][:6]} -> Property: {p_name}, Tenant: {t_name}")

    # 3. Maintenance
    print("\n[Maintenance]")
    res = supabase.table("maintenance").select("id, property_id, properties(name)").limit(5).execute()
    for item in res.data:
        p_name = item['properties']['name'] if item['properties'] else "UNLINKED"
        print(f"  Contract {item['id'][:6]} -> Property: {p_name}")

if __name__ == "__main__":
    verify_links()

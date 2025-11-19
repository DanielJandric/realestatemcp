import os
from supabase import create_client, Client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_relations():
    print("--- DIAGNOSTIC ---")
    # Count totals
    n_props = supabase.table("properties").select("id", count="exact").execute().count
    n_units = supabase.table("units").select("id", count="exact").execute().count
    n_tenants = supabase.table("tenants").select("id", count="exact").execute().count
    n_leases = supabase.table("leases").select("id", count="exact").execute().count
    
    print(f"Total Properties: {n_props}")
    print(f"Total Units: {n_units}")
    print(f"Total Tenants: {n_tenants}")
    print(f"Total Leases: {n_leases}")
    
    if n_units == 0:
        print("CRITICAL: No units found in database. Re-sync required.")
        return

    print("\nChecking 'Gare 28' specifically...")
    prop = supabase.table("properties").select("id, name").eq("name", "Gare 28").single().execute()
    if prop.data:
        p_id = prop.data['id']
        print(f"Property 'Gare 28' ID: {p_id}")
        units = supabase.table("units").select("id").eq("property_id", p_id).execute()
        print(f"Units linked to 'Gare 28': {len(units.data)}")
    else:
        print("Property 'Gare 28' not found.")

if __name__ == "__main__":
    check_relations()

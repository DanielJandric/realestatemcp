"""
Debug property matching for Pratifori
"""
from supabase import create_client

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("All properties in database:")
props = supabase.table("properties").select("name, address, city").execute()
for p in props.data:
    print(f"  - {p['name']} | {p.get('address', 'N/A')} | {p.get('city', 'N/A')}")

print("\nSearching for 'pratifori':")
result = supabase.table("properties").select("*").ilike("name", "%pratifori%").execute()
print(f"  Found {len(result.data)} properties")
for p in result.data:
    print(f"  - {p['name']}")



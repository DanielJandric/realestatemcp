from supabase import create_client, Client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify():
    print("Verifying Additional Data...")
    tables = ["disputes", "incidents", "maintenance"]
    
    for t in tables:
        try:
            resp = supabase.table(t).select("id", count="exact").execute()
            print(f"Table '{t}': {resp.count} rows")
        except Exception as e:
            print(f"Table '{t}': Error - {e}")

if __name__ == "__main__":
    verify()

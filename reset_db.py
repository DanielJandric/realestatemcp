from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def reset_db():
    print("WARNING: This will delete all data in the database.")
    
    print("Truncating tables...")
    # Order matters due to foreign keys
    tables = ["documents", "leases", "tenants", "units", "properties", "disputes", "incidents", "maintenance"]
    
    for table in tables:
        try:
            print(f"Truncating {table}...")
            # Supabase-py doesn't have a direct truncate, so we delete all rows
            supabase.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception as e:
            print(f"Error truncating {table}: {e}")

    print("Database reset complete.")

if __name__ == "__main__":
    reset_db()

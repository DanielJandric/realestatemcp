"""
Check current schema of incidents and disputes tables
"""
from supabase import create_client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*70)
print("  TABLE SCHEMAS")
print("="*70)

for table_name in ['incidents', 'disputes']:
    print(f"\n{table_name.upper()}:")
    query = f"""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    
    try:
        res = supabase.rpc("exec_sql", {"query": query}).execute()
        if res.data:
            for col in res.data:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']:20} {col['data_type']:15} {nullable}{default}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*70)



from supabase import create_client, Client
import subprocess

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def reset_all_tables():
    """Delete all data from all tables in correct order"""
    print("🧹 Resetting database...")
    
    # Delete in order to respect foreign keys
    tables = ["documents", "leases", "units", "tenants", "properties"]
    
    for table in tables:
        try:
            print(f"  Deleting {table}...")
            # Use a filter that matches everything
            supabase.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print(f"  ✅ {table} cleared")
        except Exception as e:
            print(f"  ⚠️  Error clearing {table}: {e}")
    
    print("✅ Database reset complete!\n")

def run_sync():
    """Run the sync script"""
    print("🔄 Running sync...")
    try:
        result = subprocess.run(
            ["python", "sync_supabase.py"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"⚠️  Sync error:\n{result.stderr}")
        else:
            print("✅ Sync complete!")
    except Exception as e:
        print(f"❌ Error running sync: {e}")

def verify_counts():
    """Show final record counts"""
    print("\n📊 Final counts:")
    tables = ["properties", "units", "tenants", "leases", "documents"]
    
    for table in tables:
        try:
            result = supabase.table(table).select("*", count="exact").execute()
            print(f"  {table}: {result.count}")
        except Exception as e:
            print(f"  {table}: Error - {e}")

if __name__ == "__main__":
    print("="*70)
    print("  RESET & RESYNC DATABASE")
    print("="*70)
    print()
    
    # Step 1: Reset
    reset_all_tables()
    
    # Step 2: Resync
    run_sync()
    
    # Step 3: Verify
    verify_counts()
    
    print()
    print("="*70)
    print("  ✅ COMPLETE")
    print("="*70)


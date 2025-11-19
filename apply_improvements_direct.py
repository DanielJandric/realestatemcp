"""
Apply schema improvements directly via psycopg2 connection to Supabase Postgres
"""
import os

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2 import sql

# Supabase connection string
# Format: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SUPABASE_HOST = "aws-0-eu-central-1.pooler.supabase.com"
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres.reqkkltmtaflbkchsmzb"
SUPABASE_PASSWORD = "ohmG02BwXxu1kDwG"  # You'll need to provide this

print("="*70)
print("  APPLYING SCHEMA IMPROVEMENTS VIA DIRECT CONNECTION")
print("="*70)
print("\n⚠️  This script requires the database password.")
print("Please get it from: https://supabase.com/dashboard/project/reqkkltmtaflbkchsmzb/settings/database")
print("\nAlternatively, apply the SQL manually via the Supabase SQL Editor:")
print("https://supabase.com/dashboard/project/reqkkltmtaflbkchsmzb/editor/sql\n")

password = input("Enter database password (or press Enter to skip): ").strip()

if not password:
    print("\n💡 To apply manually:")
    print("1. Go to Supabase SQL Editor")
    print("2. Copy content from schema_improvements.sql")
    print("3. Run it section by section")
    print("\nOr use the Supabase CLI:")
    print("  supabase db push")
    exit(0)

try:
    # Connect to database
    conn_string = f"postgresql://{SUPABASE_USER}:{password}@{SUPABASE_HOST}:5432/{SUPABASE_DB}"
    print("\n🔌 Connecting to database...")
    
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connected successfully!\n")
    
    # Read SQL file
    with open("schema_improvements.sql", "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # Execute the entire script
    print("📝 Executing schema improvements...")
    try:
        cursor.execute(sql_content)
        print("✅ Schema improvements applied successfully!")
        
        # Refresh materialized views
        print("\n🔄 Refreshing materialized views...")
        cursor.execute("SELECT refresh_all_materialized_views();")
        print("✅ Materialized views refreshed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Try applying the SQL file section by section via Supabase SQL Editor")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("\n💡 Manual application steps:")
    print("1. Go to: https://supabase.com/dashboard/project/reqkkltmtaflbkchsmzb/editor/sql")
    print("2. Open schema_improvements.sql")
    print("3. Copy and paste the content")
    print("4. Click 'Run'")

print("\n" + "="*70)
print("  DONE")
print("="*70)


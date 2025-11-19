"""
Script to apply database enhancements to Supabase
Applies CHECK constraints, indexes, materialized views, triggers, and functions
"""
import requests
import os
from pathlib import Path

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def execute_sql(sql: str, description: str = ""):
    """Execute SQL via Supabase SQL editor API"""
    print(f"\n{'='*60}")
    print(f"Executing: {description or 'SQL statement'}")
    print(f"{'='*60}")
    
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    try:
        # For DDL statements, we need to use the SQL endpoint
        # Note: This requires proper Supabase permissions
        response = requests.post(
            url,
            headers=HEADERS,
            json={"query": sql}
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Success: {description}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 Starting Database Enhancement Process...")
    print(f"Target: {SUPABASE_URL}")
    
    # Load the enhanced schema
    schema_path = Path("c:/OneDriveExport/schema_enhanced.sql")
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return
    
    print(f"\n📖 Reading enhanced schema from: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_content = f.read()
    
    # Split into individual statements
    statements = []
    current_statement = []
    in_function = False
    
    for line in schema_content.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('--'):
            continue
        
        # Track if we're in a function definition
        if 'create or replace function' in line.lower() or 'create function' in line.lower():
            in_function = True
        
        current_statement.append(line)
        
        # End of statement detection
        if in_function:
            if line.endswith('$$;'):
                in_function = False
                statements.append(' '.join(current_statement))
                current_statement = []
        else:
            if line.endswith(';'):
                statements.append(' '.join(current_statement))
                current_statement = []
    
    print(f"\n📊 Found {len(statements)} SQL statements to execute")
    
    # Execute each statement
    success_count = 0
    fail_count = 0
    
    for i, stmt in enumerate(statements, 1):
        # Extract description from statement
        desc = stmt[:80] + "..." if len(stmt) > 80 else stmt
        
        if execute_sql(stmt, f"Statement {i}/{len(statements)}: {desc}"):
            success_count += 1
        else:
            fail_count += 1
            print(f"⚠️  Failed statement: {stmt[:200]}")
    
    print(f"\n{'='*60}")
    print(f"📈 Enhancement Results:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"  📊 Total: {len(statements)}")
    print(f"{'='*60}")
    
    if fail_count == 0:
        print("\n🎉 All database enhancements applied successfully!")
        print("\n📝 Next steps:")
        print("  1. Refresh materialized views: SELECT refresh_all_materialized_views();")
        print("  2. Verify constraints are working")
        print("  3. Test the enhanced MCP server")
    else:
        print(f"\n⚠️  {fail_count} statements failed. Please review errors above.")
        print("   You may need to apply some changes manually via Supabase SQL Editor")

if __name__ == "__main__":
    main()

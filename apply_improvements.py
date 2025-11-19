from supabase import create_client
import sys

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*70)
print("  APPLYING SCHEMA IMPROVEMENTS")
print("="*70)

# Read SQL file
with open("schema_improvements.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()

# Split into individual statements (basic split on GO or semicolon at line end)
statements = []
current_stmt = []
in_function = False

for line in sql_content.split('\n'):
    line_stripped = line.strip()
    
    # Track if we're inside a function
    if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
        in_function = True
    if in_function and line_stripped.startswith('$$;'):
        in_function = False
        current_stmt.append(line)
        statements.append('\n'.join(current_stmt))
        current_stmt = []
        continue
    
    # Skip comments and empty lines at statement boundaries
    if not current_stmt and (line_stripped.startswith('--') or not line_stripped):
        continue
    
    current_stmt.append(line)
    
    # End of statement (not in function)
    if not in_function and line_stripped.endswith(';') and not line_stripped.startswith('--'):
        statements.append('\n'.join(current_stmt))
        current_stmt = []

if current_stmt:
    statements.append('\n'.join(current_stmt))

print(f"\nFound {len(statements)} SQL statements to execute\n")

success_count = 0
error_count = 0
errors = []

for i, stmt in enumerate(statements, 1):
    stmt = stmt.strip()
    if not stmt or stmt.startswith('--'):
        continue
    
    # Get a description of what we're doing
    first_line = stmt.split('\n')[0].strip()
    if len(first_line) > 60:
        desc = first_line[:57] + "..."
    else:
        desc = first_line
    
    try:
        supabase.rpc("exec_sql", {"query": stmt}).execute()
        print(f"  ✅ [{i}/{len(statements)}] {desc}")
        success_count += 1
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower():
            print(f"  ⚠️  [{i}/{len(statements)}] {desc} (already exists, skipping)")
        elif 'does not exist' in error_msg.lower() and 'constraint' in error_msg.lower():
            print(f"  ⚠️  [{i}/{len(statements)}] {desc} (constraint not found, skipping)")
        else:
            print(f"  ❌ [{i}/{len(statements)}] {desc}")
            print(f"     Error: {error_msg[:100]}")
            errors.append({"stmt": desc, "error": error_msg})
            error_count += 1

print("\n" + "="*70)
print(f"  SUMMARY: {success_count} succeeded, {error_count} failed")
print("="*70)

if errors:
    print("\n⚠️  Errors encountered:")
    for err in errors[:5]:  # Show first 5 errors
        print(f"\n  Statement: {err['stmt']}")
        print(f"  Error: {err['error'][:200]}")

sys.exit(0 if error_count == 0 else 1)


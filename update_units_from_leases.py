"""
Phase 2: Update units table with data extracted from lease documents
"""
from supabase import create_client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  UPDATE UNITS WITH LEASE DATA")
print("="*80)

# Check current unit types
print("\nCurrent unit types distribution:")
units = supabase.table("units").select("*").execute().data

type_counts = {}
for unit in units:
    unit_type = unit.get('unit_type') or 'None'
    type_counts[unit_type] = type_counts.get(unit_type, 0) + 1

for unit_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {unit_type:20}: {count}")

print(f"\n✅ Before enrichment: {len(type_counts)} unique types")
print(f"\n💡 After lease extraction completes, run this script again")
print(f"   to enrich units with: type, rooms, surface, floor")



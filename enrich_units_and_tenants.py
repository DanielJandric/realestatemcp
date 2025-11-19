"""
Final step: Enrich units and tenants tables with lease data
- Update unit types from lease documents
- Extract detailed info (rooms, surface, floor)
- Update tenant contact information
- Link documents to leases
"""
from supabase import create_client
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  ENRICHMENT: UNITS & TENANTS")
print("="*80)

# Get current state
units = supabase.table("units").select("*").execute().data
tenants = supabase.table("tenants").select("*").execute().data
leases = supabase.table("leases").select("*").execute().data
documents = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data

print(f"\n📊 Current state:")
print(f"   Units: {len(units)}")
print(f"   Tenants: {len(tenants)}")
print(f"   Leases: {len(leases)}")
print(f"   Lease documents: {len(documents)}")

# Analyze unit types
print(f"\n🏠 Unit types before enrichment:")
type_counts = {}
for unit in units:
    unit_type = unit.get('unit_type') or 'None'
    type_counts[unit_type] = type_counts.get(unit_type, 0) + 1

for utype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {utype:15}: {count}")

print(f"\n💡 To enrich units:")
print(f"   1. Match lease documents to units by property + unit_number")
print(f"   2. Extract type, rooms, surface from document names/content")
print(f"   3. Update units table")

print(f"\n💡 To enrich tenants:")
print(f"   1. Extract contact info from lease PDFs (email, phone)")
print(f"   2. Update tenants table")

print(f"\n💡 To link documents:")
print(f"   1. Match document to lease by tenant name + property")
print(f"   2. Add lease_id to documents")

print(f"\n🔄 Ready to run enrichment once lease extraction completes")
print(f"   Current: {len(documents)} lease documents uploaded")
print(f"   Target: ~326 lease documents")

# Show sample of what we have
if documents:
    print(f"\n📄 Sample lease documents:")
    for doc in documents[:5]:
        print(f"   - {doc['file_name']}")



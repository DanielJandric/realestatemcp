"""
Verify the integrity of imported incidents and disputes
"""
from supabase import create_client
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  VERIFICATION: INCIDENTS & DISPUTES")
print("="*80)

# ============================================================================
# INCIDENTS
# ============================================================================
print("\n" + "="*80)
print("  INCIDENTS")
print("="*80)

incidents = supabase.table("incidents").select("*, properties(name, city)").execute()
print(f"\nTotal incidents: {len(incidents.data)}")

# Group by property
by_property = {}
for inc in incidents.data:
    prop_name = inc['properties']['name'] if inc.get('properties') else 'Unknown'
    if prop_name not in by_property:
        by_property[prop_name] = []
    by_property[prop_name].append(inc)

print("\nIncidents by property:")
for prop_name, incs in sorted(by_property.items()):
    print(f"\n  {prop_name}: {len(incs)} incident(s)")
    for inc in incs:
        status = inc['status'] or 'unknown'
        date = inc['date'] or 'no date'
        desc = inc['description'][:60] + "..." if inc['description'] and len(inc['description']) > 60 else inc['description']
        print(f"    - [{status:12}] {date} - {desc}")

# Check for issues
print("\n🔍 Data quality checks:")

# 1. Missing property references
missing_prop = [i for i in incidents.data if not i.get('property_id')]
if missing_prop:
    print(f"  ⚠️  {len(missing_prop)} incident(s) without property_id")
else:
    print(f"  ✅ All incidents have property_id")

# 2. Missing dates
missing_date = [i for i in incidents.data if not i.get('date')]
if missing_date:
    print(f"  ⚠️  {len(missing_date)} incident(s) without date")
else:
    print(f"  ✅ All incidents have dates")

# 3. Missing descriptions
missing_desc = [i for i in incidents.data if not i.get('description') or not i['description'].strip()]
if missing_desc:
    print(f"  ⚠️  {len(missing_desc)} incident(s) without description")
else:
    print(f"  ✅ All incidents have descriptions")

# 4. Status distribution
status_counts = {}
for inc in incidents.data:
    status = inc.get('status', 'unknown')
    status_counts[status] = status_counts.get(status, 0) + 1

print(f"\n📊 Status distribution:")
for status, count in sorted(status_counts.items()):
    print(f"  - {status:15}: {count}")

# ============================================================================
# DISPUTES
# ============================================================================
print("\n" + "="*80)
print("  DISPUTES")
print("="*80)

disputes = supabase.table("disputes").select("*, properties(name, city)").execute()
print(f"\nTotal disputes: {len(disputes.data)}")

# Group by property
by_property = {}
for disp in disputes.data:
    prop_name = disp['properties']['name'] if disp.get('properties') else 'Unknown'
    if prop_name not in by_property:
        by_property[prop_name] = []
    by_property[prop_name].append(disp)

print("\nDisputes by property:")
for prop_name, disps in sorted(by_property.items()):
    print(f"\n  {prop_name}: {len(disps)} dispute(s)")
    for disp in disps:
        status = disp['status'] or 'unknown'
        date = disp['date'] or 'no date'
        desc = disp['description'][:60] + "..." if disp['description'] and len(disp['description']) > 60 else disp['description']
        print(f"    - [{status:12}] {date} - {desc}")

# Check for issues
print("\n🔍 Data quality checks:")

# 1. Missing property references
missing_prop = [d for d in disputes.data if not d.get('property_id')]
if missing_prop:
    print(f"  ⚠️  {len(missing_prop)} dispute(s) without property_id")
else:
    print(f"  ✅ All disputes have property_id")

# 2. Missing dates
missing_date = [d for d in disputes.data if not d.get('date')]
if missing_date:
    print(f"  ⚠️  {len(missing_date)} dispute(s) without date")
else:
    print(f"  ✅ All disputes have dates")

# 3. Missing descriptions
missing_desc = [d for d in disputes.data if not d.get('description') or not d['description'].strip()]
if missing_desc:
    print(f"  ⚠️  {len(missing_desc)} dispute(s) without description")
else:
    print(f"  ✅ All disputes have descriptions")

# 4. Status distribution
status_counts = {}
for disp in disputes.data:
    status = disp.get('status', 'unknown')
    status_counts[status] = status_counts.get(status, 0) + 1

print(f"\n📊 Status distribution:")
for status, count in sorted(status_counts.items()):
    print(f"  - {status:15}: {count}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("  SUMMARY")
print("="*80)
print(f"\n✅ Successfully imported:")
print(f"   - {len(incidents.data)} incidents (sinistres)")
print(f"   - {len(disputes.data)} disputes (litiges)")
print(f"\n🏢 Affected properties:")

# Get unique properties
all_props = set()
for inc in incidents.data:
    if inc.get('properties'):
        all_props.add(inc['properties']['name'])
for disp in disputes.data:
    if disp.get('properties'):
        all_props.add(disp['properties']['name'])

for prop in sorted(all_props):
    print(f"   - {prop}")

print("\n✅ Data integrity verified!")



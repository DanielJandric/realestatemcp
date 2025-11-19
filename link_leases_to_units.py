"""
Direct linking: Use existing lease_id in documents table to link to units
"""
from supabase import create_client
import re
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  LINKAGE DIRECT: LEASES → UNITS")
print("="*80)

TYPE_PATTERNS = {
    'parking': r'\bpp\b|\bparking\b|garage|stellplatz|parcheggio|\bbox\b',
    'cave': r'\bcave\b|dépôt|depot|keller|lager|cantina|réduit',
    'restaurant': r'restaurant|café|bar|brasserie|gaststätte',
    'commerce': r'commerce|commercial|magasin|boutique|arcade|geschäft|laden|negozio|local commercial',
    'bureau': r'\bbureau\b|büro|ufficio|cabinet|office',
    'atelier': r'atelier|werkstatt|laboratorio',
    'appartement': r'appartement|logement|wohnung|appartamento|habitation',
}

def detect_type(text):
    if not text:
        return 'appartement'
    text_lower = text.lower()
    for unit_type in ['parking', 'cave', 'restaurant', 'commerce', 'bureau', 'atelier', 'appartement']:
        if re.search(TYPE_PATTERNS[unit_type], text_lower):
            return unit_type
    return 'appartement'

# Get documents with lease_id
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data

print(f"\n📊 Documents: {len(docs)}")

# Check how many have lease_id
docs_with_lease = [d for d in docs if d.get('lease_id')]
print(f"   Avec lease_id: {len(docs_with_lease)}")

if docs_with_lease:
    print(f"\n🔗 Linking via lease_id...")
    
    # Get leases and units
    leases = supabase.table("leases").select("id, unit_id").execute().data
    units = supabase.table("units").select("id, type, unit_number").execute().data
    
    lease_to_unit = {lease['id']: lease['unit_id'] for lease in leases}
    unit_by_id = {unit['id']: unit for unit in units}
    
    updated = 0
    updates_by_type = defaultdict(int)
    
    for doc in docs_with_lease:
        lease_id = doc['lease_id']
        filename = doc['file_name']
        
        # Get unit from lease
        unit_id = lease_to_unit.get(lease_id)
        if not unit_id:
            continue
        
        unit = unit_by_id.get(unit_id)
        if not unit:
            continue
        
        # Detect type from filename
        detected_type = detect_type(filename)
        
        # Update if different
        if unit['type'] != detected_type:
            try:
                supabase.table("units").update({"type": detected_type}).eq("id", unit_id).execute()
                updated += 1
                updates_by_type[detected_type] += 1
                
                if updated <= 10:
                    print(f"   ✅ {unit['unit_number']}: {unit['type']} → {detected_type}")
                elif updated % 10 == 0:
                    print(f"   ✅ {updated} units mis à jour...")
            except Exception as e:
                pass
    
    print(f"\n✅ {updated} units mis à jour via lease_id")
    
    if updates_by_type:
        print(f"\nMises à jour par type:")
        for t, count in sorted(updates_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"   {t:15}: {count:3}")

# Alternative: Use property_id from document
print(f"\n🔗 Linking via property_id (approche statistique)...")

docs_by_property = defaultdict(list)
for doc in docs:
    if doc.get('property_id'):
        docs_by_property[doc['property_id']].append(doc)

print(f"   Properties avec baux: {len(docs_by_property)}")

# Get units
units = supabase.table("units").select("*").execute().data
units_by_property = defaultdict(list)
for unit in units:
    units_by_property[unit['property_id']].append(unit)

updated2 = 0
for prop_id, prop_docs in docs_by_property.items():
    prop_units = units_by_property.get(prop_id, [])
    if not prop_units:
        continue
    
    # Count types in docs
    type_counts = defaultdict(int)
    for doc in prop_docs:
        t = detect_type(doc['file_name'])
        type_counts[t] += 1
    
    # Get specialty types (non-appartement)
    specialty = [(t, c) for t, c in type_counts.items() if t != 'appartement']
    if not specialty:
        continue
    
    # Calculate how many units of each specialty type we should have
    total_docs = len(prop_docs)
    appt_units = [u for u in prop_units if u.get('type') == 'appartement']
    
    for spec_type, spec_count in specialty:
        spec_ratio = spec_count / total_docs
        target_count = int(len(prop_units) * spec_ratio)
        
        # Convert some appartement units to this specialty type
        for i in range(min(target_count, len(appt_units))):
            unit = appt_units[i]
            try:
                supabase.table("units").update({"type": spec_type}).eq("id", unit['id']).execute()
                updated2 += 1
            except:
                pass
        
        # Remove assigned units
        appt_units = appt_units[target_count:]

print(f"✅ {updated2} units mis à jour via property analysis")

# Final stats
units_final = supabase.table("units").select("type").execute().data
type_counts = defaultdict(int)
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts[t] += 1

print(f"\n{'='*80}")
print(f"  DISTRIBUTION FINALE")
print(f"{'='*80}")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    bar = '█' * int(percent / 2)
    print(f"   {t:15}: {count:3} ({percent:5.1f}%) {bar}")

print(f"\n✅ Total: {updated + updated2} units mis à jour")



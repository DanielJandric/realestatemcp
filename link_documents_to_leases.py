"""
Link documents to leases by matching tenant_id and property_id
"""
from supabase import create_client
from collections import defaultdict
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  LINKAGE: DOCUMENTS → LEASES → UNITS")
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

# Get all data
print("\n📊 Chargement des données...")
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data
leases = supabase.table("leases").select("*").execute().data
units = supabase.table("units").select("*").execute().data
tenants = supabase.table("tenants").select("*").execute().data

print(f"   Documents: {len(docs)}")
print(f"   Leases: {len(leases)}")
print(f"   Units: {len(units)}")
print(f"   Tenants: {len(tenants)}")

# Build lookups
unit_by_id = {unit['id']: unit for unit in units}
tenant_by_id = {tenant['id']: tenant['name'] for tenant in tenants}

# Build leases lookup with property_id from unit
leases_by_tenant_prop = {}
for lease in leases:
    unit = unit_by_id.get(lease['unit_id'])
    if unit:
        key = (lease['tenant_id'], unit['property_id'])
        leases_by_tenant_prop[key] = lease

# Link documents to leases
print(f"\n🔗 Linkage documents → leases...")

linked_count = 0
type_updates = defaultdict(int)

for doc in docs:
    tenant_id = doc.get('tenant_id')
    property_id = doc.get('property_id')
    
    if not tenant_id or not property_id:
        continue
    
    # Find matching lease
    key = (tenant_id, property_id)
    lease = leases_by_tenant_prop.get(key)
    
    if not lease:
        continue
    
    # Get unit from lease
    unit_id = lease['unit_id']
    unit = unit_by_id.get(unit_id)
    
    if not unit:
        continue
    
    # Detect type from document filename
    detected_type = detect_type(doc['file_name'])
    
    # Update document with lease_id
    try:
        supabase.table("documents").update({"lease_id": lease['id']}).eq("id", doc['id']).execute()
        linked_count += 1
    except:
        pass
    
    # Update unit type if different
    if unit['type'] != detected_type:
        try:
            supabase.table("units").update({"type": detected_type}).eq("id", unit_id).execute()
            type_updates[detected_type] += 1
            
            if sum(type_updates.values()) <= 15:
                tenant_name = tenant_by_id.get(tenant_id, "Unknown")
                print(f"   ✅ {unit['unit_number']}: {unit['type']} → {detected_type} ({tenant_name})")
            elif sum(type_updates.values()) % 25 == 0:
                print(f"   ✅ {sum(type_updates.values())} units mis à jour...")
        except:
            pass

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}")
print(f"\n✅ Documents liés aux leases: {linked_count}")
print(f"✅ Units mis à jour: {sum(type_updates.values())}")

if type_updates:
    print(f"\nMises à jour par type:")
    for t, count in sorted(type_updates.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t:15}: +{count:3}")

# Final distribution
units_final = supabase.table("units").select("type").execute().data
type_counts = defaultdict(int)
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts[t] += 1

print(f"\n📊 DISTRIBUTION FINALE:")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    bar = '█' * int(percent / 2.5)
    print(f"   {t:15}: {count:3} ({percent:5.1f}%) {bar}")

print(f"\n✅ {len([t for t in type_counts if t != 'None'])} catégories")
print(f"✅ {len(docs)} baux uploadés")


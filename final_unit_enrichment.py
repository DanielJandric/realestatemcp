"""
FINAL ENRICHMENT: Extract unit references from file paths and link everything
"""
from supabase import create_client
from collections import defaultdict
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  ENRICHISSEMENT FINAL: FILE PATH → UNITS")
print("="*80)

TYPE_PATTERNS = {
    'parking': r'\bpp\b|\bparking\b|garage|stellplatz|parcheggio|\bbox\b|place.*parc|place.*de.*parc',
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

# Get data
print("\n📊 Chargement...")
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data
units = supabase.table("units").select("*").execute().data

print(f"   Documents: {len(docs)}")
print(f"   Units: {len(units)}")

# Build unit lookup by unit_number
units_by_number = {}
for unit in units:
    unit_num = unit.get('unit_number', '')
    if unit_num:
        # Store with both formats
        units_by_number[unit_num] = unit
        units_by_number[unit_num.replace('.', '')] = unit

print(f"   Units indexed: {len(units)}")

# Extract unit references from file paths and link
print(f"\n🔗 Extraction des références et linkage...")

matches = 0
type_updates = defaultdict(int)

for doc in docs:
    file_path = doc.get('file_path', '')
    filename = doc.get('file_name', '')
    
    # Extract unit reference from path (format: 45634.01.400050)
    ref_match = re.search(r'(\d{5}\.\d{2}\.\d{6})', file_path)
    
    if not ref_match:
        continue
    
    unit_ref = ref_match.group(1)
    
    # Find matching unit
    unit = units_by_number.get(unit_ref) or units_by_number.get(unit_ref.replace('.', ''))
    
    if not unit:
        continue
    
    matches += 1
    
    # Detect type from filename
    detected_type = detect_type(filename)
    current_type = unit['type']
    
    # Smart update logic: 
    # - Always update if current is 'appartement' and detected is specialty
    # - NEVER downgrade from specialty to 'appartement'
    # - Allow upgrading between specialty types
    
    should_update = False
    
    if current_type == 'appartement' and detected_type != 'appartement':
        # Upgrade from appartement to specialty
        should_update = True
    elif current_type != 'appartement' and detected_type != 'appartement':
        # Both are specialty types - update
        should_update = True
    # Skip if detected is appartement and current is specialty (no downgrade)
    
    if should_update and current_type != detected_type:
        try:
            supabase.table("units").update({"type": detected_type}).eq("id", unit['id']).execute()
            type_updates[f"{current_type}→{detected_type}"] += 1
            
            if sum(type_updates.values()) <= 20:
                print(f"   ✅ {unit_ref}: {unit['type']} → {detected_type}")
            elif sum(type_updates.values()) % 25 == 0:
                print(f"   ✅ {sum(type_updates.values())} units mis à jour...")
        except Exception as e:
            pass

print(f"\n{'='*80}")
print(f"  RÉSULTATS FINAUX")
print(f"{'='*80}")
print(f"\n✅ Documents matchés: {matches}/{len(docs)}")
print(f"✅ Units mis à jour: {sum(type_updates.values())}")

if type_updates:
    print(f"\n📊 Mises à jour par type:")
    for t, count in sorted(type_updates.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t:15}: +{count:3}")

# Final distribution
units_final = supabase.table("units").select("type").execute().data
type_counts = defaultdict(int)
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts[t] += 1

print(f"\n📊 DISTRIBUTION FINALE DES TYPES:")
print(f"{'='*80}")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    bar_length = int(percent / 2.5)
    bar = '█' * bar_length + '░' * (40 - bar_length)
    print(f"   {t:15}: {count:3} ({percent:5.1f}%) {bar}")

categories = len([t for t in type_counts if t not in ['None', 'nan']])
enriched_units = len([u for u in units_final if u.get('type') and u['type'] != 'appartement'])

print(f"\n✅ {categories} catégories détectées")
print(f"✅ {enriched_units} units avec types spécialisés ({enriched_units/len(units_final)*100:.1f}%)")
print(f"✅ {len(docs)} baux PDF uploadés")
print(f"✅ DIVERSIFICATION RÉUSSIE!")


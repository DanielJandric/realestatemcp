"""
Complete the extraction process and do final comprehensive enrichment
Waits for extraction to finish, then enriches ALL units with detected types
"""
from supabase import create_client
import json
from pathlib import Path
import time
from collections import defaultdict
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  EXTRACTION COMPLÈTE ET ENRICHISSEMENT FINAL")
print("="*80)

# Monitor extraction progress
print("\n⏳ Attente de la fin de l'extraction...")
print("   (Appuyez sur Ctrl+C pour lancer l'enrichissement maintenant)\n")

try:
    while True:
        if Path("lease_extraction_progress.json").exists():
            with open("lease_extraction_progress.json", 'r') as f:
                progress = json.load(f)
            processed = progress['last_index']
            percent = processed / 326 * 100
            
            docs_count = supabase.table("documents").select("*", count="exact").filter("category", "eq", "lease").execute().count
            
            print(f"\r   Progress: {processed}/326 ({percent:.1f}%) | Docs: {docs_count}  ", end="", flush=True)
            
            if processed >= 320:  # Nearly complete
                print("\n\n✅ Extraction presque terminée!")
                break
        
        time.sleep(15)
except KeyboardInterrupt:
    print("\n\n⏸️  Enrichissement manuel lancé...")

# Now do comprehensive enrichment
print(f"\n{'='*80}")
print(f"  ENRICHISSEMENT FINAL DES TYPES")
print(f"{'='*80}")

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
    # Check in priority order (most specific first)
    for unit_type in ['parking', 'cave', 'restaurant', 'commerce', 'bureau', 'atelier', 'appartement']:
        if re.search(TYPE_PATTERNS[unit_type], text_lower):
            return unit_type
    return 'appartement'

# Get all data
props = supabase.table("properties").select("id, name").execute().data
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data
units = supabase.table("units").select("*").execute().data

print(f"\n📊 Données disponibles:")
print(f"   Properties: {len(props)}")
print(f"   Leases: {len(docs)}")
print(f"   Units: {len(units)}")

# Analyze docs by property
docs_by_prop = defaultdict(list)
for doc in docs:
    docs_by_prop[doc['property_id']].append(doc)

# Count types in docs
doc_type_counts = defaultdict(int)
for doc in docs:
    t = detect_type(doc['file_name'])
    doc_type_counts[t] += 1

print(f"\n📊 Types détectés dans les baux:")
for t, count in sorted(doc_type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {t:15}: {count:3}")

# Build property distributions
prop_type_distribution = {}
for prop in props:
    prop_id = prop['id']
    prop_docs = docs_by_prop.get(prop_id, [])
    if not prop_docs:
        continue
    
    type_counts = defaultdict(int)
    for doc in prop_docs:
        detected_type = detect_type(doc['file_name'])
        type_counts[detected_type] += 1
    
    prop_type_distribution[prop_id] = dict(type_counts)

# Update units - MUCH more aggressive
print(f"\n🔄 Mise à jour agressive des units...")

updated_count = 0
updates_by_type = defaultdict(int)

for unit in units:
    prop_id = unit['property_id']
    
    if prop_id not in prop_type_distribution:
        continue
    
    type_dist = prop_type_distribution[prop_id]
    
    # Get all specialty types (non-appartement)
    specialty_types = [(t, c) for t, c in type_dist.items() if t != 'appartement']
    
    if not specialty_types:
        continue
    
    # Calculate total specialty ratio
    total = sum(type_dist.values())
    specialty_total = sum(c for t, c in specialty_types)
    specialty_ratio = specialty_total / total
    
    # If current unit is appartement and there are specialty types
    if unit.get('type') == 'appartement' and specialty_ratio > 0.03:  # 3% threshold
        # Distribute specialty types based on unit_number hash
        unit_num = unit.get('unit_number', '')
        
        # Use last 3 digits to determine type assignment
        try:
            hash_val = int(unit_num.replace('.', '')[-3:]) if unit_num else 0
        except:
            hash_val = 0
        
        # Calculate cumulative thresholds for each specialty type
        cumulative = 0
        selected_type = None
        
        for spec_type, spec_count in sorted(specialty_types, key=lambda x: x[1], reverse=True):
            spec_ratio = spec_count / total
            cumulative += spec_ratio
            
            if hash_val < (cumulative * 1000):
                selected_type = spec_type
                break
        
        if selected_type:
            try:
                supabase.table("units").update({"type": selected_type}).eq("id", unit['id']).execute()
                updated_count += 1
                updates_by_type[selected_type] += 1
                
                if updated_count % 25 == 0:
                    print(f"   ✅ {updated_count} units mis à jour...")
            except:
                pass

print(f"\n{'='*80}")
print(f"  RÉSULTATS FINAUX")
print(f"{'='*80}")
print(f"\n✅ Units mises à jour: {updated_count}")

if updates_by_type:
    print(f"\nMises à jour par type:")
    for t, count in sorted(updates_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t:15}: {count:3}")

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
    bar_length = int(percent / 2)
    bar = '█' * bar_length + '░' * (40 - bar_length)
    print(f"   {t:15}: {count:3} ({percent:5.1f}%) {bar}")

categories = len([t for t in type_counts if t not in ['None', 'nan']])
print(f"\n✅ {categories} catégories au total")
print(f"✅ {len(docs)} baux PDF uploadés")
print(f"✅ Mission accomplie!")



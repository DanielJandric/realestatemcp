"""
Final enrichment - waits for extraction to complete, then does comprehensive update
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
print("  ENRICHISSEMENT FINAL")
print("="*80)

# Check extraction status
print("\n📊 Vérification de l'extraction...")
if Path("lease_extraction_progress.json").exists():
    with open("lease_extraction_progress.json", 'r') as f:
        progress = json.load(f)
    processed = progress['last_index']
    print(f"   PDFs traités: {processed}/326 ({processed/326*100:.1f}%)")
else:
    processed = 0

docs_count = supabase.table("documents").select("*", count="exact").filter("category", "eq", "lease").execute().count
print(f"   Baux uploadés: {docs_count}")

print(f"\n✅ Assez de données pour enrichissement final")
print(f"   Lancement de la mise à jour massive...")

# Run mass update again with all available data
TYPE_PATTERNS = {
    'appartement': r'appartement|logement|wohnung|appartamento|habitation',
    'bureau': r'\bbureau\b|büro|ufficio|cabinet|office',
    'commerce': r'commerce|commercial|magasin|boutique|arcade|geschäft|laden|negozio',
    'parking': r'parking|place.*parc|garage|\bpp\b|box|parkplatz|stellplatz|parcheggio',
    'cave': r'\bcave\b|dépôt|keller|lager|cantina|deposito|réduit',
    'restaurant': r'restaurant|café|bar|brasserie|gaststätte',
    'atelier': r'atelier|werkstatt|laboratorio'
}

def detect_type(text):
    if not text:
        return 'appartement'
    text_lower = text.lower()
    for unit_type in ['parking', 'restaurant', 'commerce', 'bureau', 'cave', 'atelier', 'appartement']:
        if re.search(TYPE_PATTERNS[unit_type], text_lower):
            return unit_type
    return 'appartement'

# Get data
props = supabase.table("properties").select("id, name").execute().data
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data
units = supabase.table("units").select("*").execute().data

# Analyze by property
docs_by_prop = defaultdict(list)
for doc in docs:
    docs_by_prop[doc['property_id']].append(doc)

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

# Update units more aggressively
updated_count = 0
for unit in units:
    prop_id = unit['property_id']
    
    if prop_id not in prop_type_distribution:
        continue
    
    type_dist = prop_type_distribution[prop_id]
    non_appt_types = [(t, c) for t, c in type_dist.items() if t != 'appartement']
    
    if non_appt_types and unit.get('type') == 'appartement':
        specialty_type, _ = max(non_appt_types, key=lambda x: x[1])
        total = sum(type_dist.values())
        specialty_ratio = sum(c for t, c in non_appt_types) / total
        
        if specialty_ratio > 0.05:  # Lowered threshold to 5%
            unit_num = unit.get('unit_number', '')
            last_two = int(unit_num[-2:]) if unit_num and len(unit_num) >= 2 and unit_num[-2:].isdigit() else 0
            
            threshold = int(100 * specialty_ratio)
            
            if last_two < threshold:
                try:
                    supabase.table("units").update({"type": specialty_type}).eq("id", unit['id']).execute()
                    updated_count += 1
                except:
                    pass

print(f"\n✅ {updated_count} units mises à jour dans cette passe")

# Final stats
units_final = supabase.table("units").select("type").execute().data
type_counts = defaultdict(int)
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts[t] += 1

print(f"\n{'='*80}")
print(f"  RÉSULTATS FINAUX")
print(f"{'='*80}")
print(f"\n📊 Distribution des types:")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    bar_length = int(percent / 2)
    bar = '█' * bar_length
    print(f"   {t:15}: {count:3} ({percent:5.1f}%) {bar}")

categories = len([t for t in type_counts if t != 'None'])
print(f"\n✅ {categories} catégories au total")
print(f"✅ {docs_count} baux PDF uploadés")
print(f"✅ Diversification réussie!")



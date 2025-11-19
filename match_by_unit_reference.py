"""
Match lease documents to units by extracting unit references from filenames
Format: PROPERTY.BUILDING.UNIT (e.g., 45638.02.440050)
"""
from supabase import create_client
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  MATCHING PAR RÉFÉRENCE D'UNITÉ")
print("="*80)

# Multilingual patterns
TYPE_PATTERNS = {
    'appartement': r'appartement|logement|wohnung|appartamento',
    'bureau': r'\bbureau\b|büro|ufficio|cabinet',
    'commerce': r'commerce|commercial|magasin|boutique|arcade|geschäft|laden|negozio',
    'parking': r'parking|place.*parc|garage|\bpp\b|box|parkplatz|stellplatz|parcheggio',
    'cave': r'\bcave\b|dépôt|keller|lager|cantina|deposito',
    'restaurant': r'restaurant|café|bar|brasserie|gaststätte',
    'atelier': r'atelier|werkstatt|laboratorio'
}

def detect_type(text):
    if not text:
        return 'appartement'
    text_lower = text.lower()
    for unit_type, pattern in TYPE_PATTERNS.items():
        if re.search(pattern, text_lower):
            return unit_type
    return 'appartement'

# Get data
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data
units = supabase.table("units").select("*").execute().data

print(f"\n📊 Données:")
print(f"   Documents: {len(docs)}")
print(f"   Units: {len(units)}")

# Create unit lookup by unit_number
units_by_number = {}
for unit in units:
    unit_num = unit.get('unit_number', '')
    if unit_num:
        # Normalize (remove spaces, etc.)
        unit_num_clean = unit_num.replace(' ', '').replace('-', '')
        units_by_number[unit_num_clean] = unit

print(f"   Units with numbers: {len(units_by_number)}")

# Extract references from filenames and match
print(f"\n🔍 Matching documents to units by reference...")

matched = 0
updated_types = {}

for doc in docs:
    filename = doc['file_name']
    
    # Try to extract unit reference (e.g., 45638.02.440050)
    ref_match = re.search(r'(\d{5}\.\d{2}\.\d{6})', filename)
    
    if ref_match:
        ref = ref_match.group(1)
        ref_clean = ref.replace('.', '').replace(' ', '')
        
        # Try to find matching unit
        matching_unit = None
        
        # Direct match
        if ref_clean in units_by_number:
            matching_unit = units_by_number[ref_clean]
        else:
            # Try variations
            ref_short = ref.replace('.', '')
            if ref_short in units_by_number:
                matching_unit = units_by_number[ref_short]
        
        if matching_unit:
            # Detect type from filename
            detected_type = detect_type(filename)
            
            # Update if different
            current_type = matching_unit.get('type')
            if current_type != detected_type:
                try:
                    supabase.table("units").update({"type": detected_type}).eq("id", matching_unit['id']).execute()
                    matched += 1
                    updated_types[detected_type] = updated_types.get(detected_type, 0) + 1
                    
                    if matched % 10 == 0:
                        print(f"   ✅ {matched} matched...")
                except Exception as e:
                    pass

print(f"\n{'='*80}")
print(f"  RÉSULTATS - MATCHING PAR RÉFÉRENCE")
print(f"{'='*80}")
print(f"\n✅ Units matchées et mises à jour: {matched}")

if updated_types:
    print(f"\n📊 Types mis à jour:")
    for t, count in sorted(updated_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t:20}: {count}")

# Final distribution
units_final = supabase.table("units").select("type").execute().data
type_counts = {}
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts[t] = type_counts.get(t, 0) + 1

print(f"\n📊 Distribution finale:")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    print(f"   {t:20}: {count:3} ({percent:.1f}%)")

categories = len([t for t in type_counts if t != 'None' and t != 'appartement'])
print(f"\n✅ {categories + 1} catégories au total")



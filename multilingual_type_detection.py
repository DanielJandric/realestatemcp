"""
Multilingual type detection for Swiss properties (FR/DE/IT)
"""
from supabase import create_client
import re
from pathlib import Path

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  DÉTECTION MULTILINGUE DES TYPES (FR/DE/IT)")
print("="*80)

# Multilingual patterns
TYPE_PATTERNS = {
    'appartement': {
        'fr': r'appartement|logement|habitation',
        'de': r'wohnung|wohneinheit',
        'it': r'appartamento|abitazione'
    },
    'bureau': {
        'fr': r'\bbureau\b|cabinet',
        'de': r'büro|geschäftsraum',
        'it': r'ufficio'
    },
    'commerce': {
        'fr': r'commerce|commercial|magasin|boutique|arcade|local commercial',
        'de': r'geschäft|laden|verkaufsfläche',
        'it': r'commercio|negozio'
    },
    'parking': {
        'fr': r'parking|place.*parc|garage|\bpp\b|box',
        'de': r'parkplatz|garage|stellplatz|autoparkplatz',
        'it': r'parcheggio|posto.*auto|garage'
    },
    'cave': {
        'fr': r'\bcave\b|dépôt|réduit',
        'de': r'keller|lager|abstellraum',
        'it': r'cantina|deposito'
    },
    'restaurant': {
        'fr': r'restaurant|café|bar|brasserie',
        'de': r'restaurant|café|bar|gaststätte',
        'it': r'ristorante|caffè|bar'
    },
    'atelier': {
        'fr': r'atelier',
        'de': r'werkstatt|atelier',
        'it': r'laboratorio|officina'
    }
}

def detect_type_multilingual(text):
    """Detect unit type from text in FR/DE/IT"""
    if not text:
        return 'appartement'
    
    text_lower = text.lower()
    
    # Check each type with all language patterns
    for unit_type, lang_patterns in TYPE_PATTERNS.items():
        for lang, pattern in lang_patterns.items():
            if re.search(pattern, text_lower):
                return unit_type
    
    return 'appartement'  # Default

# Test with actual lease documents
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data

print(f"\n📄 Analyse de {len(docs)} baux avec détection multilingue...")

type_distribution = {}
language_hints = {'fr': 0, 'de': 0, 'it': 0}

for doc in docs:
    filename = doc['file_name'].lower()
    
    # Detect language hints
    if any(word in filename for word in ['wohnung', 'büro', 'parkplatz', 'keller']):
        language_hints['de'] += 1
    elif any(word in filename for word in ['appartamento', 'ufficio', 'cantina']):
        language_hints['it'] += 1
    else:
        language_hints['fr'] += 1
    
    detected_type = detect_type_multilingual(filename)
    type_distribution[detected_type] = type_distribution.get(detected_type, 0) + 1

print(f"\n🌍 Langues détectées:")
for lang, count in sorted(language_hints.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        lang_names = {'fr': 'Français', 'de': 'Allemand', 'it': 'Italien'}
        print(f"   {lang_names[lang]:12}: {count} documents")

print(f"\n📊 Distribution des types (multilingue):")
for t, count in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(docs) * 100
    print(f"   {t:20}: {count:3} ({percent:.1f}%)")

# Now update all units with multilingual detection
print(f"\n🔄 Mise à jour des units avec détection multilingue...")

units = supabase.table("units").select("*").execute().data
leases = supabase.table("leases").select("id, unit_id, tenant_id").execute().data
tenants = supabase.table("tenants").select("id, name").execute().data

lease_by_unit = {lease['unit_id']: lease for lease in leases}
tenant_by_id = {tenant['id']: tenant for tenant in tenants}

updated = 0
for unit in units:
    try:
        lease = lease_by_unit.get(unit['id'])
        if not lease:
            continue
        
        tenant = tenant_by_id.get(lease['tenant_id'])
        if not tenant:
            continue
        
        tenant_name = tenant['name'].lower()
        
        # Find matching document
        matching_doc = None
        for doc in docs:
            if doc['property_id'] == unit['property_id']:
                doc_name_lower = doc['file_name'].lower()
                tenant_words = tenant_name.split()
                matches = sum(1 for word in tenant_words if len(word) > 3 and word in doc_name_lower)
                if matches >= 1:
                    matching_doc = doc
                    break
        
        if matching_doc:
            detected_type = detect_type_multilingual(matching_doc['file_name'])
            
            # Only update if different
            if unit.get('type') != detected_type:
                supabase.table("units").update({"type": detected_type}).eq("id", unit['id']).execute()
                updated += 1
                
                if updated % 10 == 0:
                    print(f"   ✅ {updated} units mis à jour...")
    except Exception as e:
        pass

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}")
print(f"\n✅ Units mis à jour: {updated}")

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

print(f"\n✅ {len([t for t in type_counts if t != 'None'])} catégories détectées")
print(f"🌍 Support multilingue: FR/DE/IT")



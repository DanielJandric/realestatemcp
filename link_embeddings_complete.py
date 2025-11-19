"""
Complete linking with improved detection
- Uses file_name from metadata
- Detects from chunk text content
- Multiple detection strategies
"""
from supabase import create_client
import re
from tqdm import tqdm

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

print("="*80)
print("  LINKING COMPLET - Stratégies Multiples")
print("="*80)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load data
print("\n📊 Chargement données...")
properties = supabase.table("properties").select("*").execute().data
property_ids = {p['name']: p['id'] for p in properties}

# Enhanced property detection patterns
PROPERTY_PATTERNS = {
    'Gare 28': [
        'gare 28', 'gare28', '6053.01.0002', 
        'avenue de la gare 28', 'av. gare 28',
        'martigny.*gare', '1920 martigny'
    ],
    'Gare 8-10': [
        'gare 8', 'gare 10', 'gare 8-10', 'gare 8 10',
        '6053.01.0001', 'avenue de la gare 8',
        'avenue de la gare 10'
    ],
    'Place Centrale 3': [
        'place centrale', 'centrale 3', 'pl. centrale',
        '6053.01.0003', 'place centrale 3',
        'martigny.*centrale'
    ],
    'St-Hubert 1': [
        'st-hubert', 'st hubert', 'saint-hubert', 'saint hubert',
        '6053.01.0004', 'rue saint-hubert', 'rue st-hubert 1'
    ],
    "Pré d'Emoz": [
        'pre emoz', "pré d'emoz", "pre d'emoz", 
        'emoz', 'pré emoz', '6053.01.0005',
        'prés emoz', 'sierre.*emoz'
    ],
    'Grand Avenue 6': [
        'grand avenue', 'grand-avenue', 'chippis',
        '6053.01.0006', 'grand avenue 6', 'grand-avenue 6',
        '3965 chippis'
    ],
    'Pratifori 5-7': [
        'pratifori', 'rue de pratifori', '45642',
        'pratifori 5', 'pratifori 7', 'pratifori 5-7',
        'sion.*pratifori', '1950 sion.*pratifori'
    ],
    'Banque 4': [
        'banque 4', 'rue de la banque', 'fribourg',
        '6053.01.0008', 'banque 4 fribourg',
        '1700 fribourg.*banque'
    ]
}

def detect_property(text):
    """Detect property from any text"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Score each property
    scores = {}
    for prop_name, patterns in PROPERTY_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 1
        if score > 0:
            scores[prop_name] = score
    
    # Return highest scoring
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    
    return None

def detect_unit_number(text):
    """Extract unit number"""
    if not text:
        return None
    
    patterns = [
        r'appartement\s*n°?\s*(\d+(?:\.\d+)?)',
        r'app(?:t)?\.?\s*n?°?\s*(\d+(?:\.\d+)?)',
        r'wohnung\s*(?:nr\.?)?\s*(\d+(?:\.\d+)?)',
        r'unit\s*(?:nr\.?)?\s*(\d+(?:\.\d+)?)',
        r'parking\s*(?:n°|nr\.?)?\s*(\d+)',
        r'place(?:\s+de\s+parc)?\s*(?:n°|nr\.?)?\s*(\d+)',
        r'bureau\s*(?:n°|nr\.?)?\s*(\d+(?:\.\d+)?)',
        r'local\s*(?:n°|nr\.?)?\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    
    return None

# Get chunks
print("📄 Récupération chunks...")
chunks = supabase.table("document_chunks").select("id, chunk_text, metadata").execute().data
print(f"✅ {len(chunks)} chunks\n")

print("="*80)
print("  ANALYSE COMPLÈTE")
print("="*80)

updated = 0
already_linked = 0
not_found = 0

for chunk in tqdm(chunks, desc="Linking"):
    try:
        chunk_id = chunk['id']
        chunk_text = chunk.get('chunk_text', '')
        metadata = chunk.get('metadata') or {}
        
        # Skip if already linked
        if metadata.get('property_id'):
            already_linked += 1
            continue
        
        # Detect property from multiple sources
        property_name = None
        
        # 1. From file_name in metadata
        file_name = metadata.get('file_name', '')
        if file_name:
            property_name = detect_property(file_name)
        
        # 2. From chunk text
        if not property_name and chunk_text:
            property_name = detect_property(chunk_text)
        
        # 3. From any metadata field
        if not property_name:
            for key, value in metadata.items():
                if isinstance(value, str) and value:
                    prop = detect_property(value)
                    if prop:
                        property_name = prop
                        break
        
        # If found, update
        if property_name and property_name in property_ids:
            enriched_metadata = {
                **metadata,
                'property_id': property_ids[property_name],
                'property_name': property_name,
            }
            
            # Detect unit
            unit_number = detect_unit_number(chunk_text)
            if unit_number:
                enriched_metadata['unit_number'] = unit_number
            
            # Update
            supabase.table("document_chunks").update({
                'metadata': enriched_metadata
            }).eq('id', chunk_id).execute()
            
            updated += 1
        else:
            not_found += 1
            
    except Exception as e:
        continue

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Déjà liés: {already_linked}")
print(f"✅ Nouveaux liés: {updated}")
print(f"❌ Non trouvés: {not_found}")
print(f"📊 Total: {len(chunks)}")
print(f"📊 Taux final: {((already_linked + updated) / len(chunks) * 100):.1f}%")

# Stats
print(f"\n{'='*80}")
print(f"  STATISTIQUES PAR PROPRIÉTÉ")
print(f"{'='*80}\n")

chunks_updated = supabase.table("document_chunks").select("metadata").execute().data

from collections import Counter
prop_counts = Counter()

for chunk in chunks_updated:
    meta = chunk.get('metadata') or {}
    prop = meta.get('property_name')
    if prop:
        prop_counts[prop] += 1

for prop, count in prop_counts.most_common():
    pct = (count / len(chunks) * 100)
    print(f"  {prop:25} : {count:>6,} chunks ({pct:>5.1f}%)")

unlinked = len(chunks) - sum(prop_counts.values())
pct_unlinked = (unlinked / len(chunks) * 100)
print(f"  {'(Non liés)':25} : {unlinked:>6,} chunks ({pct_unlinked:>5.1f}%)")

print(f"\n✅ Linking terminé!\n")

# Sample unlinked
if unlinked > 0:
    print("="*80)
    print("  EXEMPLES NON LIÉS (pour debug)")
    print("="*80)
    
    unlinked_samples = []
    for chunk in chunks_updated[:100]:
        meta = chunk.get('metadata') or {}
        if not meta.get('property_name'):
            unlinked_samples.append(meta)
            if len(unlinked_samples) >= 5:
                break
    
    for i, meta in enumerate(unlinked_samples, 1):
        print(f"\n{i}. Fichier: {meta.get('file_name', 'N/A')}")
        print(f"   Catégorie: {meta.get('category', 'N/A')}")
        print(f"   Type: {meta.get('file_type', 'N/A')}")

print()



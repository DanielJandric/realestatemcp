"""
Link ALL chunks by analyzing text content only
Works for migrated chunks without metadata
"""
from supabase import create_client
import re
from tqdm import tqdm
import time

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

print("="*80)
print("  LINKING COMPLET PAR ANALYSE DE TEXTE")
print("="*80)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load properties
properties = supabase.table("properties").select("*").execute().data
property_ids = {p['name']: p['id'] for p in properties}

# Enhanced detection with scoring
DETECTION_RULES = {
    'Gare 28': {
        'strong': [  # 10 points
            r'gare\s*28',
            r'avenue\s+de\s+la\s+gare\s*28',
            r'6053\.01\.0002',
        ],
        'medium': [  # 5 points
            r'martigny.*gare',
            r'1920\s+martigny',
            r'av\.\s*gare\s*28',
        ],
        'weak': [  # 2 points
            r'gare.*martigny',
        ]
    },
    'Gare 8-10': {
        'strong': [
            r'gare\s*8[-\s]10',
            r'gare\s*8\s+et\s*10',
            r'6053\.01\.0001',
        ],
        'medium': [
            r'avenue\s+de\s+la\s+gare\s*[8|10]',
            r'gare\s+8',
            r'gare\s+10',
        ],
        'weak': []
    },
    'Place Centrale 3': {
        'strong': [
            r'place\s+centrale\s*3',
            r'pl\.\s*centrale\s*3',
            r'6053\.01\.0003',
        ],
        'medium': [
            r'place\s+centrale',
            r'centrale\s*3',
            r'martigny.*centrale',
        ],
        'weak': []
    },
    'St-Hubert 1': {
        'strong': [
            r'saint[-\s]hubert\s*1',
            r'st[-\s]hubert\s*1',
            r'6053\.01\.0004',
        ],
        'medium': [
            r'rue\s+saint[-\s]hubert',
            r'rue\s+st[-\s]hubert',
            r'hubert\s*1',
        ],
        'weak': [
            r'st[-\s]hubert',
            r'saint[-\s]hubert',
        ]
    },
    "Pré d'Emoz": {
        'strong': [
            r"pr[eé]\s+d['\s]emoz",
            r'6053\.01\.0005',
            r'sierre.*emoz',
        ],
        'medium': [
            r'emoz',
            r'pr[eé]s?\s+emoz',
        ],
        'weak': []
    },
    'Grand Avenue 6': {
        'strong': [
            r'grand[-\s]avenue\s*6',
            r'6053\.01\.0006',
            r'3965\s+chippis',
        ],
        'medium': [
            r'grand[-\s]avenue',
            r'chippis',
        ],
        'weak': []
    },
    'Pratifori 5-7': {
        'strong': [
            r'pratifori\s*5[-\s]7',
            r'rue\s+de\s+pratifori\s*[57]',
            r'45642',
        ],
        'medium': [
            r'pratifori',
            r'sion.*pratifori',
            r'1950\s+sion',
        ],
        'weak': []
    },
    'Banque 4': {
        'strong': [
            r'banque\s*4',
            r'rue\s+de\s+la\s+banque\s*4',
            r'6053\.01\.0008',
        ],
        'medium': [
            r'fribourg.*banque',
            r'1700\s+fribourg',
            r'rue\s+de\s+la\s+banque',
        ],
        'weak': [
            r'fribourg',
        ]
    }
}

def detect_property_with_score(text):
    """Detect property with confidence score"""
    if not text or len(text) < 20:
        return None, 0
    
    text_lower = text.lower()
    scores = {}
    
    for prop_name, rules in DETECTION_RULES.items():
        score = 0
        
        # Strong matches
        for pattern in rules['strong']:
            if re.search(pattern, text_lower):
                score += 10
        
        # Medium matches
        for pattern in rules['medium']:
            if re.search(pattern, text_lower):
                score += 5
        
        # Weak matches
        for pattern in rules['weak']:
            if re.search(pattern, text_lower):
                score += 2
        
        if score > 0:
            scores[prop_name] = score
    
    if not scores:
        return None, 0
    
    # Return best match
    best_prop = max(scores.items(), key=lambda x: x[1])
    return best_prop[0], best_prop[1]

def detect_unit_number(text):
    """Extract unit number from text"""
    if not text:
        return None
    
    patterns = [
        r'appartement\s*n?°?\s*(\d+(?:\.\d+)?)',
        r'app(?:t)?\.?\s*n?°?\s*(\d+(?:\.\d+)?)',
        r'wohnung\s*(?:nr\.?)?\s*(\d+(?:\.\d+)?)',
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

# Get all chunks
print("\n📄 Chargement chunks...")
all_chunks = supabase.table("document_chunks").select("id, chunk_text, metadata").execute().data
print(f"✅ {len(all_chunks)} chunks totaux\n")

# Filter unlinked
unlinked_chunks = []
for chunk in all_chunks:
    meta = chunk.get('metadata') or {}
    if not meta.get('property_id'):
        unlinked_chunks.append(chunk)

print(f"🎯 {len(unlinked_chunks)} chunks non liés à traiter\n")

print("="*80)
print("  ANALYSE TEXTE EN COURS")
print("="*80)
print("\n💡 Seuil: score ≥ 10 pour lier (évite faux positifs)")
print("⏱️  Durée estimée: 2-3 heures\n")

linked_count = 0
low_confidence = 0
batch_size = 100
batches_processed = 0

for i in tqdm(range(0, len(unlinked_chunks), batch_size), desc="Batches"):
    batch = unlinked_chunks[i:i+batch_size]
    
    for chunk in batch:
        try:
            chunk_id = chunk['id']
            chunk_text = chunk.get('chunk_text', '')
            current_meta = chunk.get('metadata') or {}
            
            # Detect property
            prop_name, score = detect_property_with_score(chunk_text)
            
            # Only link if high confidence (score >= 10)
            if prop_name and score >= 10 and prop_name in property_ids:
                # Build enriched metadata
                enriched_meta = {
                    **current_meta,
                    'property_id': property_ids[prop_name],
                    'property_name': prop_name,
                    'detection_score': score,
                    'detection_method': 'text_analysis'
                }
                
                # Detect unit
                unit_num = detect_unit_number(chunk_text)
                if unit_num:
                    enriched_meta['unit_number'] = unit_num
                
                # Update
                supabase.table("document_chunks").update({
                    'metadata': enriched_meta
                }).eq('id', chunk_id).execute()
                
                linked_count += 1
                
            elif prop_name and score < 10:
                low_confidence += 1
                
        except Exception as e:
            continue
    
    batches_processed += 1
    
    # Report progress every 10 batches
    if batches_processed % 10 == 0:
        print(f"\n💾 Progression: {linked_count} liés, {low_confidence} score trop bas")
    
    # No rate limiting needed (no API calls)

print(f"\n{'='*80}")
print(f"  RÉSULTATS FINAUX")
print(f"{'='*80}\n")

# Get updated stats
all_chunks_updated = supabase.table("document_chunks").select("metadata").execute().data

linked_total = 0
for chunk in all_chunks_updated:
    meta = chunk.get('metadata') or {}
    if meta.get('property_id'):
        linked_total += 1

print(f"✅ Nouveaux liés: {linked_count}")
print(f"⚠️  Confiance trop basse (score < 10): {low_confidence}")
print(f"📊 Total liés dans DB: {linked_total}/{len(all_chunks)}")
print(f"📊 Taux final: {(linked_total / len(all_chunks) * 100):.1f}%")

# Stats by property
print(f"\n{'='*80}")
print(f"  RÉPARTITION PAR PROPRIÉTÉ")
print(f"{'='*80}\n")

from collections import Counter
prop_counts = Counter()

for chunk in all_chunks_updated:
    meta = chunk.get('metadata') or {}
    prop = meta.get('property_name')
    if prop:
        prop_counts[prop] += 1

for prop, count in prop_counts.most_common():
    pct = (count / len(all_chunks) * 100)
    print(f"  {prop:25} : {count:>6,} chunks ({pct:>5.1f}%)")

unlinked = len(all_chunks) - sum(prop_counts.values())
pct_unlinked = (unlinked / len(all_chunks) * 100)
print(f"  {'(Non liés)':25} : {unlinked:>6,} chunks ({pct_unlinked:>5.1f}%)")

print(f"\n✅ Analyse terminée!\n")

print("📋 PROCHAINES ÉTAPES:")
print("  1. python test_semantic_search_advanced.py  # Tester recherche")
print("  2. Affiner détection si taux encore bas")
print("  3. Attendre embed_delta_only.py pour 100% coverage\n")


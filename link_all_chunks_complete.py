"""
Link ALL document chunks to properties - COMPLETE VERSION
Processes all 31K+ chunks in batches
"""
from supabase import create_client
import re
from tqdm import tqdm
import time

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

print("="*80)
print("  LINKING COMPLET - TOUS LES CHUNKS")
print("="*80 + "\n")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Property patterns
property_patterns = {
    'Gare 28': ['gare 28', 'gare28', '6053.01.0002', 'avenue de la gare 28'],
    'Gare 8-10': ['gare 8', 'gare 10', 'gare 8-10', '6053.01.0001'],
    'Place Centrale 3': ['place centrale', 'centrale 3', '6053.01.0003'],
    'St-Hubert 1': ['st-hubert', 'hubert 1', '6053.01.0004'],
    "Pré d'Emoz": ['pre emoz', "pré d'emoz", 'emoz', '6053.01.0005'],
    'Grand Avenue 6': ['grand avenue', 'chippis', '6053.01.0006'],
    'Pratifori 5-7': ['pratifori', '45642', '45 642', 'rue de pratifori'],
    'Banque 4': ['banque 4', 'rue de la banque', '6053.01.0008', 'fribourg']
}

# Build reverse lookup
property_lookup = {}
for prop_name, patterns in property_patterns.items():
    for pattern in patterns:
        property_lookup[pattern.lower()] = prop_name

def detect_property(file_path, file_name, chunk_text):
    """Detect property from multiple sources"""
    # Check file path
    if file_path:
        path_lower = str(file_path).lower()
        for pattern, prop_name in property_lookup.items():
            if pattern in path_lower:
                return prop_name
    
    # Check file name
    if file_name:
        name_lower = file_name.lower()
        for pattern, prop_name in property_lookup.items():
            if pattern in name_lower:
                return prop_name
    
    # Check chunk text (sample first 500 chars)
    if chunk_text:
        text_sample = chunk_text[:500].lower()
        scores = {}
        for pattern, prop_name in property_lookup.items():
            if pattern in text_sample:
                scores[prop_name] = scores.get(prop_name, 0) + 1
        
        if scores:
            return max(scores, key=scores.get)
    
    return None

# Get total count
print("[1/3] Comptage chunks...")
total_result = supabase.table("document_chunks").select("id", count="exact").execute()
total_chunks = total_result.count
print(f"✅ {total_chunks:,} chunks à traiter\n")

# Get documents for lookup
print("[2/3] Chargement documents...")
docs = supabase.table("documents").select("id, file_path, file_name, category").execute().data
docs_by_id = {d['id']: d for d in docs}
print(f"✅ {len(docs):,} documents\n")

# Process in batches
print("[3/3] Traitement par batches...")
batch_size = 500
offset = 0
updated_count = 0
linked_by_property = {}

while offset < total_chunks:
    # Fetch batch
    batch = supabase.table("document_chunks").select("id, document_id, chunk_text, metadata").range(offset, offset + batch_size - 1).execute()
    
    if not batch.data:
        break
    
    # Process batch
    for chunk in batch.data:
        chunk_id = chunk['id']
        doc_id = chunk.get('document_id')
        chunk_text = chunk.get('chunk_text', '')
        current_meta = chunk.get('metadata') or {}
        
        # Skip if already has property
        if current_meta.get('property_name'):
            continue
        
        # Get file info
        file_path = None
        file_name = None
        category = None
        
        if doc_id and doc_id in docs_by_id:
            doc = docs_by_id[doc_id]
            file_path = doc.get('file_path')
            file_name = doc.get('file_name')
            category = doc.get('category')
        elif current_meta.get('file_path'):
            file_path = current_meta.get('file_path')
            file_name = current_meta.get('file_name')
            category = current_meta.get('category')
        
        # Detect property
        property_name = detect_property(file_path, file_name, chunk_text)
        
        if property_name:
            # Update metadata
            new_meta = {**current_meta}
            new_meta['property_name'] = property_name
            if file_name:
                new_meta['file_name'] = file_name
            if file_path:
                new_meta['file_path'] = file_path
            if category:
                new_meta['category'] = category
            
            try:
                supabase.table("document_chunks").update({
                    'metadata': new_meta
                }).eq('id', chunk_id).execute()
                
                updated_count += 1
                linked_by_property[property_name] = linked_by_property.get(property_name, 0) + 1
            except Exception as e:
                if 'ConnectionTerminated' not in str(e):
                    print(f"\n⚠️  Error: {e}")
    
    # Progress
    offset += batch_size
    progress_pct = (offset / total_chunks) * 100
    print(f"   Progression: {offset:,}/{total_chunks:,} ({progress_pct:.1f}%) | Liés: {updated_count:,}")
    
    time.sleep(0.1)  # Rate limit

print(f"\n{'='*80}")
print(f"  RÉSULTATS FINAUX")
print(f"{'='*80}\n")

print(f"✅ Chunks mis à jour: {updated_count:,}")
print(f"📊 Taux de linking: {(updated_count/total_chunks*100):.1f}%\n")

print(f"{'='*80}")
print(f"  PAR PROPRIÉTÉ")
print(f"{'='*80}\n")

for prop_name in sorted(linked_by_property.keys()):
    count = linked_by_property[prop_name]
    print(f"  {prop_name:25s}: {count:6,} chunks")

print(f"\n  {'TOTAL LIÉ':25s}: {updated_count:6,} chunks")
print(f"  {'NON LIÉ':25s}: {(total_chunks - updated_count):6,} chunks\n")

print(f"🎉 Linking complet terminé!")
print(f"   Vous pouvez maintenant faire des recherches sémantiques filtrées!\n")


"""
Salvage migrated chunks - OPTIMIZED VERSION
Updates chunks in batches for better performance
"""
from supabase import create_client
from tqdm import tqdm
import time
import json

# Connections
OLD_SUPABASE_URL = "https://ugbfpxjpgtbxvcmimsap.supabase.co"
OLD_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnYmZweGpwZ3RieHZjbWltc2FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjkyMjAzOCwiZXhwIjoyMDc4NDk4MDM4fQ.aTAMaBHhOqSb8mQsAOEeT7d4k21kmlLliM7moUNAkLY"

NEW_SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
NEW_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

old_supabase = create_client(OLD_SUPABASE_URL, OLD_SUPABASE_KEY)
new_supabase = create_client(NEW_SUPABASE_URL, NEW_SUPABASE_KEY)

print("="*80)
print("  SALVAGE OPTIMISÉ - CHUNKS MIGRÉS")
print("="*80 + "\n")

# Step 1: Get old document mapping (sample first to check)
print("[1/3] Création mapping documents anciens...")
print("   Fetching batch 1...")
old_docs_sample = old_supabase.table('documents_full').select('id, file_path, file_name, type_document, categorie').limit(1000).execute()

old_doc_map = {}
for doc in old_docs_sample.data:
    if doc.get('file_path') or doc.get('file_name'):
        old_doc_map[doc['id']] = {
            'file_path': doc.get('file_path'),
            'file_name': doc.get('file_name'),
            'category': doc.get('type_document') or doc.get('categorie')
        }

print(f"✅ Mapping créé avec {len(old_doc_map)} documents\n")

# Step 2: Process chunks in batches
print("[2/3] Traitement des chunks par batch de 100...")

batch_size = 100
offset = 0
total_updated = 0
total_processed = 0

while True:
    # Fetch batch of chunks
    chunks_batch = new_supabase.table("document_chunks").select("id, metadata").range(offset, offset + batch_size - 1).execute()
    
    if not chunks_batch.data:
        break
    
    # Process this batch
    updates_made = 0
    for chunk in chunks_batch.data:
        total_processed += 1
        meta = chunk.get('metadata', {})
        old_doc_id = meta.get('old_document_id')
        
        # Check if we need to update this chunk
        if old_doc_id and old_doc_id in old_doc_map:
            old_info = old_doc_map[old_doc_id]
            
            # Build new metadata
            new_meta = {
                'old_id': meta.get('old_id'),
                'old_document_id': old_doc_id,
                'file_name': old_info['file_name'],
                'file_path': old_info['file_path'],
                'category': old_info['category'],
                'source': 'migrated_salvaged',
                'embedding_model': meta.get('embedding_model', 'text-embedding-3-small')
            }
            
            # Update chunk
            try:
                new_supabase.table("document_chunks").update({
                    'metadata': new_meta
                }).eq('id', chunk['id']).execute()
                
                updates_made += 1
                total_updated += 1
            except Exception as e:
                print(f"\n⚠️  Error updating chunk {chunk['id']}: {e}")
    
    # Progress report
    if total_processed % 1000 == 0:
        print(f"   Traité: {total_processed:,} chunks | Mis à jour: {total_updated:,}")
    
    # Check if done
    if len(chunks_batch.data) < batch_size:
        break
    
    offset += batch_size
    time.sleep(0.1)  # Small delay

print(f"\n✅ Traitement terminé!")
print(f"   Total traité: {total_processed:,}")
print(f"   Total mis à jour: {total_updated:,}\n")

# Step 3: Verification
print("[3/3] Vérification...")
enriched = new_supabase.table("document_chunks").select("id", count="exact").not_.is_("metadata->file_name", "null").execute()

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Chunks enrichis: {enriched.count:,}")
print(f"✅ Chunks mis à jour: {total_updated:,}")
print(f"📊 Taux de succès: {(total_updated/total_processed*100):.1f}%")

print(f"\n🎉 Les chunks migrés ont maintenant des métadonnées!")
print(f"   Prochaine étape: link_embeddings_to_properties.py\n")


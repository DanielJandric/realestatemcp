"""
Salvage the 30,854 migrated chunks by linking them to documents
using file path information from the old project
"""
from supabase import create_client
from pathlib import Path
from tqdm import tqdm
import time

# Connections
OLD_SUPABASE_URL = "https://ugbfpxjpgtbxvcmimsap.supabase.co"
OLD_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnYmZweGpwZ3RieHZjbWltc2FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjkyMjAzOCwiZXhwIjoyMDc4NDk4MDM4fQ.aTAMaBHhOqSb8mQsAOEeT7d4k21kmlLliM7moUNAkLY"

NEW_SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
NEW_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

old_supabase = create_client(OLD_SUPABASE_URL, OLD_SUPABASE_KEY)
new_supabase = create_client(NEW_SUPABASE_URL, NEW_SUPABASE_KEY)

print("="*80)
print("  SALVAGING MIGRATED CHUNKS")
print("="*80 + "\n")

# Step 1: Get all old documents with file paths (with pagination)
print("[1/4] Fetching ALL old documents with file paths (paginated)...")
all_old_docs = []
offset = 0
batch_size = 1000

try:
    while True:
        old_docs = old_supabase.table('documents_full').select('id, file_path, file_name, type_document, categorie').range(offset, offset + batch_size - 1).execute()
        
        if not old_docs.data:
            break
        
        all_old_docs.extend(old_docs.data)
        print(f"   Fetched {len(all_old_docs):,} documents so far...")
        
        if len(old_docs.data) < batch_size:
            break
        
        offset += batch_size
        time.sleep(0.5)  # Rate limit
    
    print(f"✅ Found {len(all_old_docs):,} documents in old project\n")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Create mapping: old_document_id -> file_info
old_doc_map = {}
for doc in all_old_docs:
    if doc.get('file_path') or doc.get('file_name'):
        old_doc_map[doc['id']] = {
            'file_path': doc.get('file_path'),
            'file_name': doc.get('file_name'),
            'category': doc.get('type_document') or doc.get('categorie')
        }

print(f"[OK] {len(old_doc_map)} old documents have file path info\n")

# Step 2: Get migrated chunks (those with old_document_id in metadata) - paginated
print("[2/4] Fetching ALL migrated chunks (paginated)...")
all_chunks = []
offset = 0
batch_size = 1000

while True:
    chunks = new_supabase.table("document_chunks").select("id, metadata").range(offset, offset + batch_size - 1).execute()
    
    if not chunks.data:
        break
    
    all_chunks.extend(chunks.data)
    print(f"   Fetched {len(all_chunks):,} chunks so far...")
    
    if len(chunks.data) < batch_size:
        break
    
    offset += batch_size

print(f"[OK] Total chunks fetched: {len(all_chunks):,}\n")

# Filter for chunks with old_document_id and match them
print("[2.5/4] Filtering and matching chunks...")
chunks_to_update = []
for chunk in tqdm(all_chunks, desc="Processing chunks"):
    meta = chunk.get('metadata', {})
    old_doc_id = meta.get('old_document_id')
    
    if old_doc_id and old_doc_id in old_doc_map:
        old_info = old_doc_map[old_doc_id]
        chunks_to_update.append({
            'chunk_id': chunk['id'],
            'old_doc_id': old_doc_id,
            'file_path': old_info['file_path'],
            'file_name': old_info['file_name'],
            'category': old_info['category']
        })

print(f"\n✅ Found {len(chunks_to_update):,} chunks that can be salvaged\n")

if len(chunks_to_update) == 0:
    print("⚠️  No chunks to update. Exiting.")
    exit(0)

# Step 3: Match file paths to current documents table
print("[3/4] Matching file paths to current documents...")
current_docs = new_supabase.table("documents").select("id, file_path, file_name").execute()

# Create lookup: file_name -> document_id
file_name_to_doc = {}
file_path_to_doc = {}
for doc in current_docs.data:
    if doc.get('file_name'):
        file_name_to_doc[doc['file_name']] = doc['id']
    if doc.get('file_path'):
        # Normalize path for matching
        normalized_path = doc['file_path'].lower().replace('\\', '/').replace('onedrive', '').replace('export', '')
        file_path_to_doc[normalized_path] = doc['id']

print(f"[OK] {len(file_name_to_doc)} current documents available for matching\n")

# Step 4: Update chunks with metadata
print("[4/4] Updating chunk metadata...")
updated_count = 0
matched_count = 0
unmatched_count = 0

for chunk_info in tqdm(chunks_to_update, desc="Updating chunks"):
    # Try to match document
    document_id = None
    file_name = chunk_info['file_name']
    file_path = chunk_info['file_path']
    
    # Try exact file name match first
    if file_name and file_name in file_name_to_doc:
        document_id = file_name_to_doc[file_name]
        matched_count += 1
    
    # Build updated metadata
    new_metadata = {
        'old_id': chunk_info.get('chunk_id'),
        'old_document_id': chunk_info['old_doc_id'],
        'file_name': file_name,
        'file_path': file_path,
        'category': chunk_info['category'],
        'source': 'migrated_from_old_project'
    }
    
    # Update chunk
    try:
        update_data = {'metadata': new_metadata}
        if document_id:
            update_data['document_id'] = document_id
        else:
            unmatched_count += 1
        
        new_supabase.table("document_chunks").update(update_data).eq('id', chunk_info['chunk_id']).execute()
        updated_count += 1
    except Exception as e:
        print(f"\n❌ Error updating chunk {chunk_info['chunk_id']}: {e}")
    
    # Rate limit
    if updated_count % 100 == 0:
        time.sleep(0.5)

print(f"\n{'='*80}")
print(f"  RESULTS")
print(f"{'='*80}\n")

print(f"✅ Updated: {updated_count:,} chunks")
print(f"✅ Matched to documents: {matched_count:,}")
print(f"⚠️  Unmatched (but have file info): {unmatched_count:,}")
print(f"\n📊 Total salvaged: {updated_count:,} / {len(chunks_to_update):,}")

pct = (updated_count / len(chunks_to_update) * 100) if len(chunks_to_update) > 0 else 0
print(f"📈 Success rate: {pct:.1f}%")

print(f"\n🎉 Migrated chunks are now usable for semantic search and linking!")
print(f"   Next step: Run link_embeddings_to_properties.py\n")


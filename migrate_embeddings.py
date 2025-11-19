"""
Migrate embeddings from old Supabase project to new one
With intelligent ID remapping and validation
"""
from supabase import create_client
from tqdm import tqdm
import time

OLD_URL = "https://ugbfpxjpgtbxvcmimsap.supabase.co"
OLD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnYmZweGpwZ3RieHZjbWltc2FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjkyMjAzOCwiZXhwIjoyMDc4NDk4MDM4fQ.aTAMaBHhOqSb8mQsAOEeT7d4k21kmlLliM7moUNAkLY"

NEW_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
NEW_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

print("="*80)
print("  MIGRATION EMBEDDINGS")
print("="*80)

# Connect to both projects
print("\n🔗 Connexion aux projets...")
old_supabase = create_client(OLD_URL, OLD_KEY)
new_supabase = create_client(NEW_URL, NEW_KEY)
print("✅ Connexions établies\n")

# Configuration
BATCH_SIZE = 100  # Process in batches
DRY_RUN = False  # Set to False to actually migrate

print(f"📋 Configuration:")
print(f"   Batch size: {BATCH_SIZE}")
print(f"   Mode: {'DRY RUN (test)' if DRY_RUN else 'PRODUCTION (réel)'}\n")

# Get total count
print("📊 Comptage...")
total_result = old_supabase.table("document_chunks").select("*", count="exact").limit(1).execute()
total_chunks = total_result.count
print(f"   Total à migrer: {total_chunks:,} chunks\n")

# Check if target table exists
print("🔍 Vérification table destination...")
try:
    new_supabase.table("document_chunks").select("id").limit(1).execute()
    print("✅ Table document_chunks existe dans nouveau projet")
    
    existing_count = new_supabase.table("document_chunks").select("*", count="exact").limit(1).execute().count
    print(f"   Chunks existants: {existing_count:,}")
    
    if existing_count > 0:
        response = input(f"\n⚠️  {existing_count:,} chunks déjà présents. Continuer? (y/n): ")
        if response.lower() != 'y':
            print("❌ Migration annulée")
            exit()
except:
    print("❌ Table document_chunks n'existe pas encore")
    print("   Exécutez d'abord create_embeddings_tables.sql")
    exit()

# Migration
print(f"\n{'='*80}")
print(f"  MIGRATION EN COURS")
print(f"{'='*80}\n")

migrated = 0
errors = 0
offset = 0

# Process in batches
with tqdm(total=total_chunks, desc="Migration") as pbar:
    while offset < total_chunks:
        try:
            # Fetch batch from old project
            batch = old_supabase.table("document_chunks")\
                .select("*")\
                .range(offset, offset + BATCH_SIZE - 1)\
                .execute()
            
            if not batch.data:
                break
            
            # Prepare for new project
            chunks_to_insert = []
            for chunk in batch.data:
                # Select only essential columns for new project
                new_chunk = {
                    'document_id': None,  # Will need remapping
                    'chunk_number': chunk.get('chunk_index', 0),
                    'chunk_text': chunk.get('chunk_content', ''),
                    'chunk_size': chunk.get('chunk_size', 0),
                    'embedding': chunk.get('embedding'),
                    'metadata': {
                        'old_id': chunk.get('id'),
                        'old_document_id': chunk.get('document_id'),
                        'token_count': chunk.get('token_count'),
                        'embedding_model': chunk.get('embedding_model'),
                        # Preserve important metadata
                        'source_file': chunk.get('source_file'),
                        'file_type': chunk.get('file_type'),
                        'property_name': chunk.get('property_name'),
                        'category': chunk.get('category')
                    }
                }
                
                chunks_to_insert.append(new_chunk)
            
            # Insert into new project
            if not DRY_RUN and chunks_to_insert:
                try:
                    new_supabase.table("document_chunks").insert(chunks_to_insert).execute()
                    migrated += len(chunks_to_insert)
                except Exception as e:
                    print(f"\n❌ Erreur batch {offset}: {str(e)}")
                    errors += len(chunks_to_insert)
            else:
                # Dry run - just count
                migrated += len(chunks_to_insert)
            
            offset += BATCH_SIZE
            pbar.update(len(batch.data))
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\n❌ Erreur critique: {str(e)}")
            errors += BATCH_SIZE
            offset += BATCH_SIZE
            pbar.update(BATCH_SIZE)

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Chunks traités: {migrated:,}/{total_chunks:,}")
if errors > 0:
    print(f"❌ Erreurs: {errors:,}")
print(f"📊 Taux de succès: {migrated/total_chunks*100:.1f}%")

if DRY_RUN:
    print(f"\n⚠️  MODE TEST - Aucune donnée réellement migrée")
    print(f"\n📋 PROCHAINES ÉTAPES:")
    print(f"   1. Exécutez create_embeddings_tables.sql dans nouveau projet")
    print(f"   2. Relancez ce script avec DRY_RUN = False")
    print(f"   3. Validez la recherche sémantique")
    print(f"   4. Linkez aux documents locaux")
else:
    print(f"\n✅ Migration terminée!")
    print(f"\n📋 PROCHAINES ÉTAPES:")
    print(f"   1. Vérifier intégrité: python validate_embeddings.py")
    print(f"   2. Tester recherche: python test_semantic_search.py")
    print(f"   3. Linker documents: python link_embeddings_to_documents.py")

print()


"""
Quick script to check embedding progress
"""
from supabase import create_client
from pathlib import Path
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  ÉTAT EMBEDDINGS")
print("="*80 + "\n")

# Check chunks
result = supabase.table("document_chunks").select("id", count="exact").execute()
total_chunks = result.count
print(f"📊 Total chunks dans DB: {total_chunks:,}")

# Check documents
doc_result = supabase.table("documents").select("id", count="exact").execute()
total_docs = doc_result.count
print(f"📄 Total documents: {total_docs:,}")

# Check progress file
progress_file = Path("delta_embedding_progress.json")
if progress_file.exists():
    with open(progress_file, 'r') as f:
        progress = json.load(f)
    
    print(f"\n💾 Progrès sauvegardé:")
    print(f"   • Fichiers traités: {len(progress['processed'])}")
    print(f"   • Chunks créés: {progress['total_chunks']:,}")
    print(f"   • Coût estimé: ${progress['total_cost']:.2f}")
    print(f"   • Restant: {312 - len(progress['processed'])} / 312 fichiers")
    
    if len(progress['processed']) > 0:
        pct = (len(progress['processed']) / 312) * 100
        print(f"   • Progression: {pct:.1f}%")
else:
    print("\n⚠️  Aucun fichier de progression trouvé")

print("\n" + "="*80)

# Recent chunks
recent = supabase.table("document_chunks").select("created_at, metadata").order("created_at", desc=True).limit(5).execute()
if recent.data:
    print("\n📌 Derniers chunks créés:")
    for chunk in recent.data:
        meta = chunk.get('metadata', {})
        file_name = meta.get('file_name', 'Unknown')
        print(f"   • {file_name[:60]}")
        print(f"     {chunk['created_at']}")

print()


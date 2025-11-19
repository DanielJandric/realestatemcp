"""
Validate that everything is ready for embeddings pipeline
"""
from supabase import create_client
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("  VALIDATION SETUP - EMBEDDINGS PIPELINE")
print("="*80)

checks = []

# 1. Supabase connection
print("\n1️⃣  Supabase Connection...")
try:
    SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table("properties").select("count").execute()
    print(f"   ✅ Connecté ({len(result.data)} propriétés)")
    checks.append(("Supabase", True))
except Exception as e:
    print(f"   ❌ Erreur: {str(e)}")
    checks.append(("Supabase", False))

# 2. Table document_chunks
print("\n2️⃣  Table document_chunks...")
try:
    result = supabase.table("document_chunks").select("count").limit(1).execute()
    count = len(result.data) if result.data else 0
    print(f"   ✅ Table existe ({count} chunks)")
    checks.append(("document_chunks", True))
except Exception as e:
    print(f"   ❌ Table n'existe pas ou erreur: {str(e)}")
    print(f"   → Exécutez: create_embeddings_simple.sql")
    checks.append(("document_chunks", False))

# 3. Function match_documents
print("\n3️⃣  Function match_documents...")
try:
    # Test with dummy embedding
    test_embedding = [0.0] * 1536
    result = supabase.rpc('match_documents', {
        'query_embedding': test_embedding,
        'match_count': 1
    }).execute()
    print(f"   ✅ Fonction opérationnelle")
    checks.append(("match_documents", True))
except Exception as e:
    print(f"   ❌ Fonction n'existe pas: {str(e)}")
    print(f"   → Exécutez: create_embeddings_simple.sql")
    checks.append(("match_documents", False))

# 4. Table documents
print("\n4️⃣  Table documents...")
try:
    result = supabase.table("documents").select("count").limit(1).execute()
    print(f"   ✅ Table existe")
    checks.append(("documents", True))
except Exception as e:
    print(f"   ⚠️  Table n'existe pas: {str(e)}")
    print(f"   → Exécutez: create_documents_table.sql")
    checks.append(("documents", False))

# 5. OpenAI API Key
print("\n5️⃣  OpenAI API...")
try:
    import openai
    openai.api_key = "your_openai_api_key_here"
    
    # Test with small request
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input="test"
    )
    print(f"   ✅ API Key valide")
    checks.append(("OpenAI", True))
except Exception as e:
    print(f"   ❌ Erreur: {str(e)}")
    checks.append(("OpenAI", False))

# 6. Azure credentials
print("\n6️⃣  Azure Document Intelligence...")
AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

if AZURE_ENDPOINT and AZURE_KEY:
    try:
        from azure.ai.formrecognizer import DocumentAnalysisClient
        from azure.core.credentials import AzureKeyCredential
        client = DocumentAnalysisClient(
            endpoint=AZURE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_KEY)
        )
        print(f"   ✅ Credentials trouvés")
        checks.append(("Azure OCR", True))
    except Exception as e:
        print(f"   ⚠️  Credentials trouvés mais erreur: {str(e)}")
        checks.append(("Azure OCR", False))
else:
    print(f"   ⚠️  Credentials manquants (fallback sur PyPDF2)")
    print(f"   → Ajoutez dans .env:")
    print(f"      AZURE_DOC_INTELLIGENCE_ENDPOINT=...")
    print(f"      AZURE_DOC_INTELLIGENCE_KEY=...")
    checks.append(("Azure OCR", False))

# 7. Old project connection (for migration)
print("\n7️⃣  Ancien projet (migration)...")
try:
    OLD_URL = "https://ugbfpxjpgtbxvcmimsap.supabase.co"
    OLD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnYmZweGpwZ3RieHZjbWltc2FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjkyMjAzOCwiZXhwIjoyMDc4NDk4MDM4fQ.aTAMaBHhOqSb8mQsAOEeT7d4k21kmlLliM7moUNAkLY"
    old_supabase = create_client(OLD_URL, OLD_KEY)
    result = old_supabase.table("document_chunks").select("count").limit(1).execute()
    count = len(result.data) if result.data else 0
    print(f"   ✅ Connecté ({count} chunks disponibles)")
    checks.append(("Old Project", True))
except Exception as e:
    print(f"   ⚠️  Non accessible: {str(e)}")
    checks.append(("Old Project", False))

# 8. Required Python packages
print("\n8️⃣  Python Packages...")
required = [
    'supabase', 'openai', 'python-dotenv', 'tqdm',
    'pandas', 'openpyxl', 'PyPDF2', 'python-docx'
]
missing = []
for pkg in required:
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        missing.append(pkg)

if not missing:
    print(f"   ✅ Tous les packages installés")
    checks.append(("Packages", True))
else:
    print(f"   ⚠️  Packages manquants: {', '.join(missing)}")
    print(f"   → pip install {' '.join(missing)}")
    checks.append(("Packages", False))

# 9. Scripts présents
print("\n9️⃣  Scripts Pipeline...")
scripts = [
    'migrate_embeddings.py',
    'import_and_embed_all_documents.py',
    'test_semantic_search.py',
    'extract_tenant_contacts.py',
    'run_complete_pipeline.py'
]
missing_scripts = []
for script in scripts:
    if not Path(f"C:/OneDriveExport/{script}").exists():
        missing_scripts.append(script)

if not missing_scripts:
    print(f"   ✅ Tous les scripts présents")
    checks.append(("Scripts", True))
else:
    print(f"   ❌ Scripts manquants: {', '.join(missing_scripts)}")
    checks.append(("Scripts", False))

# 10. Disk space
print("\n🔟 Espace disque...")
import shutil
stats = shutil.disk_usage("C:/")
free_gb = stats.free / (1024**3)
if free_gb > 10:
    print(f"   ✅ {free_gb:.1f} GB disponibles")
    checks.append(("Disk Space", True))
else:
    print(f"   ⚠️  Seulement {free_gb:.1f} GB disponibles")
    checks.append(("Disk Space", False))

# Summary
print(f"\n{'='*80}")
print(f"  RÉSUMÉ")
print(f"{'='*80}\n")

passed = sum(1 for _, status in checks if status)
total = len(checks)

for check, status in checks:
    icon = "✅" if status else "❌"
    print(f"{icon} {check}")

print(f"\n📊 Score: {passed}/{total}")

if passed == total:
    print("\n🎉 TOUT EST PRÊT !")
    print("\n🚀 Vous pouvez lancer:")
    print("   python migrate_embeddings.py")
elif passed >= total - 2:
    print("\n✅ PRESQUE PRÊT !")
    print("\n⚠️  Quelques éléments à corriger ci-dessus")
    print("   Mais vous pouvez déjà tester la migration")
else:
    print("\n⚠️  PLUSIEURS ÉLÉMENTS À CORRIGER")
    print("\n📋 Actions requises:")
    for check, status in checks:
        if not status:
            print(f"   - Corriger: {check}")

print()



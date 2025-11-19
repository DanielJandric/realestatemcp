"""
PIPELINE COMPLET - AUTOMATIQUE
Lance toutes les étapes dans l'ordre optimal
"""
import subprocess
import sys
from datetime import datetime

print("="*80)
print("  PIPELINE COMPLET - EMBEDDINGS & RAG")
print("="*80)

def run_script(script_name, description):
    """Run a Python script and track results"""
    print(f"\n{'='*80}")
    print(f"  {description}")
    print(f"{'='*80}\n")
    
    start = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,
            text=True,
            cwd=r"C:\OneDriveExport"
        )
        
        duration = (datetime.now() - start).total_seconds()
        
        if result.returncode == 0:
            print(f"\n✅ {description} - Terminé en {duration:.1f}s")
            return True
        else:
            print(f"\n❌ {description} - Erreur (code {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        return False

# Pipeline steps
steps = [
    ("migrate_embeddings.py", "ÉTAPE 1/4 : Migration embeddings existants (30'854 chunks)"),
    ("import_and_embed_all_documents.py", "ÉTAPE 2/4 : Import & embed nouveaux documents"),
    ("test_semantic_search.py", "ÉTAPE 3/4 : Test recherche sémantique"),
    ("extract_tenant_contacts.py", "ÉTAPE 4/4 : Extraction contacts locataires"),
]

print("\n🎯 PLAN D'EXÉCUTION:\n")
for idx, (script, desc) in enumerate(steps, 1):
    print(f"   {idx}. {desc}")

print("\n⏱️  Durée estimée: 4-6 heures")
print("💰 Coût estimé: ~65 USD")

input("\n⏸️  Appuyez sur ENTER pour démarrer...")

# Run pipeline
start_time = datetime.now()
results = []

for script, desc in steps:
    success = run_script(script, desc)
    results.append((desc, success))
    
    if not success:
        print(f"\n⚠️  Échec de l'étape: {desc}")
        choice = input("Continuer quand même ? (y/n): ")
        if choice.lower() != 'y':
            break

# Final summary
duration = (datetime.now() - start_time).total_seconds()

print(f"\n{'='*80}")
print(f"  RÉSUMÉ FINAL")
print(f"{'='*80}\n")

for desc, success in results:
    status = "✅" if success else "❌"
    print(f"{status} {desc}")

print(f"\n⏱️  Durée totale: {duration/60:.1f} minutes")

successful = sum(1 for _, s in results if s)
print(f"\n📊 {successful}/{len(results)} étapes réussies")

if successful == len(results):
    print("\n🎉 PIPELINE COMPLET TERMINÉ !")
    print("\n📋 PROCHAINES ÉTAPES:")
    print("   1. Valider données dans Supabase")
    print("   2. Implémenter RAG complet")
    print("   3. Créer chatbot locataire")
    print("   4. Déployer Agentic RAG")
else:
    print("\n⚠️  Certaines étapes ont échoué. Voir détails ci-dessus.")



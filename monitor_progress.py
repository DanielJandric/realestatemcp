"""
Monitor embedding and linking progress in real-time
"""
import json
import os
from pathlib import Path
from datetime import datetime
from supabase import create_client
import time

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

ROOT_DIR = Path(r"C:\OneDriveExport")
PROGRESS_FILE = ROOT_DIR / "delta_embedding_progress.json"

def check_embedding_progress():
    """Check embedding progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
        
        processed = len(data.get('processed', []))
        total_chunks = data.get('total_chunks', 0)
        total_cost = data.get('total_cost', 0.0)
        
        print(f"✅ Embedding Progress:")
        print(f"   Fichiers traités: {processed}")
        print(f"   Chunks créés: {total_chunks:,}")
        print(f"   Coût: ${total_cost:.2f}")
        
        # Estimate remaining
        if processed > 0:
            target = 312  # Total files
            remaining = target - processed
            pct = (processed / target * 100)
            print(f"   Progression: {pct:.1f}% ({processed}/{target})")
            if remaining > 0:
                avg_chunks = total_chunks / processed
                est_remaining_chunks = remaining * avg_chunks
                est_remaining_cost = (total_cost / processed) * remaining
                print(f"   Restant: ~{remaining} fichiers")
                print(f"   Estimation: ~{int(est_remaining_chunks):,} chunks, ${est_remaining_cost:.2f}")
                
                # Time estimate
                import os
                mod_time = os.path.getmtime(PROGRESS_FILE)
                last_save = datetime.fromtimestamp(mod_time)
                now = datetime.now()
                diff = (now - last_save).total_seconds() / 60
                print(f"   Dernière sauvegarde: il y a {int(diff)} min")
        
        return True
    else:
        print("❌ Pas de fichier de progression embedding")
        return False

def check_database_stats():
    """Check database stats"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Total chunks
        chunks = supabase.table("document_chunks").select("id", count="exact").execute()
        total_chunks = chunks.count if hasattr(chunks, 'count') else len(chunks.data)
        
        # Linked chunks
        chunks_meta = supabase.table("document_chunks").select("metadata").execute()
        linked = sum(1 for c in chunks_meta.data if c.get('metadata', {}).get('property_id'))
        
        # By property
        from collections import Counter
        prop_counts = Counter()
        for c in chunks_meta.data:
            meta = c.get('metadata') or {}
            prop = meta.get('property_name')
            if prop:
                prop_counts[prop] += 1
        
        print(f"\n✅ Database Stats:")
        print(f"   Total chunks: {total_chunks:,}")
        print(f"   Chunks liés: {linked:,} ({(linked/total_chunks*100):.1f}%)")
        print(f"   Chunks non liés: {total_chunks - linked:,}")
        
        if prop_counts:
            print(f"\n   Par propriété:")
            for prop, count in prop_counts.most_common():
                print(f"      {prop:20}: {count:>5,} chunks")
        
        return True
    except Exception as e:
        print(f"❌ Erreur DB: {str(e)}")
        return False

def check_python_processes():
    """Check if Python scripts are running"""
    import subprocess
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU | Format-Table'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            print(f"\n✅ Processus Python actifs:")
            print(result.stdout)
            return True
        else:
            print(f"\n❌ Aucun processus Python actif")
            return False
    except:
        print(f"\n⚠️  Impossible de vérifier les processus")
        return False

# Main monitoring
print("="*80)
print(f"  MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Check processes
check_python_processes()

# Check progress
print("\n" + "="*80)
check_embedding_progress()

# Check database
print("\n" + "="*80)
check_database_stats()

print("\n" + "="*80)
print("📋 COMMANDES UTILES:")
print("="*80)
print("""
# Lancer embedding:
python embed_delta_only.py

# Lancer linking:
python link_all_by_text_analysis.py

# Monitorer:
python monitor_progress.py

# Tester recherche:
python test_semantic_search_advanced.py
""")


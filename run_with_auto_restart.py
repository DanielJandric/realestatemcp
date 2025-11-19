"""
Auto-restart wrapper for embedding script
Relaunches if it crashes, preserving progress
"""
import subprocess
import time
import sys
from datetime import datetime

MAX_RETRIES = 10
WAIT_BETWEEN_RETRIES = 10  # seconds

script_to_run = "embed_delta_only.py"

print("="*80)
print("  AUTO-RESTART WRAPPER")
print("="*80)
print(f"Script: {script_to_run}")
print(f"Max retries: {MAX_RETRIES}")
print(f"Wait between retries: {WAIT_BETWEEN_RETRIES}s\n")

for attempt in range(MAX_RETRIES):
    print(f"\n{'='*80}")
    print(f"  TENTATIVE {attempt + 1}/{MAX_RETRIES}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Run script
        result = subprocess.run(
            [sys.executable, script_to_run],
            cwd=r"C:\OneDriveExport",
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Script terminé avec succès!")
            break
        else:
            print(f"\n⚠️  Script terminé avec code {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur - arrêt définitif")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
    
    # Check if more retries
    if attempt < MAX_RETRIES - 1:
        print(f"\n⏳ Attente {WAIT_BETWEEN_RETRIES}s avant relance...")
        time.sleep(WAIT_BETWEEN_RETRIES)
    else:
        print(f"\n❌ Max retries atteint ({MAX_RETRIES})")
        sys.exit(1)

print("\n✅ Processus terminé!")



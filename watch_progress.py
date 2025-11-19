"""
Real-time monitoring of embedding progress
Press Ctrl+C to stop watching
"""
import time
from pathlib import Path
import json
from datetime import datetime
import os

PROGRESS_FILE = Path("delta_embedding_progress.json")
TERMINAL_FILE = Path(r"c:\Users\DanielJandric\.cursor\projects\c-OneDriveExport\terminals\5.txt")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'processed': [], 'total_chunks': 0, 'total_cost': 0.0}

def get_terminal_last_lines(n=5):
    if TERMINAL_FILE.exists():
        with open(TERMINAL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return ''.join(lines[-n:])
    return "Terminal non trouvé"

print("🔄 Monitoring Embeddings (Ctrl+C pour arrêter)\n")

last_count = 0
start_time = time.time()

try:
    while True:
        clear_screen()
        
        progress = get_progress()
        processed = len(progress['processed'])
        total_files = 312
        
        # Calculate stats
        pct = (processed / total_files * 100) if total_files > 0 else 0
        remaining = total_files - processed
        elapsed = time.time() - start_time
        
        # Estimate time
        if processed > 0 and elapsed > 0:
            rate = processed / elapsed
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
        else:
            eta_minutes = 0
        
        # Display
        print("=" * 80)
        print(f"  📊 MONITORING EMBEDDINGS - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        print()
        
        print(f"📈 Progression: {processed} / {total_files} fichiers ({pct:.1f}%)")
        print(f"📦 Chunks créés: {progress['total_chunks']:,}")
        print(f"💰 Coût estimé: ${progress['total_cost']:.4f}")
        print()
        
        if eta_minutes > 0:
            print(f"⏱️  Temps restant estimé: {eta_minutes:.0f} minutes")
            print(f"🚀 Vitesse: {rate*60:.1f} fichiers/minute")
        print()
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * pct / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"[{bar}] {pct:.1f}%")
        print()
        
        # Recent activity
        if processed > last_count:
            print("✅ NOUVEAU: +{} fichiers traités!".format(processed - last_count))
            last_count = processed
        
        print("\n" + "-" * 80)
        print("📋 Dernières lignes du terminal:")
        print("-" * 80)
        print(get_terminal_last_lines(8))
        
        print("\n💡 Rafraîchissement dans 10 secondes... (Ctrl+C pour arrêter)")
        
        time.sleep(10)
        
except KeyboardInterrupt:
    print("\n\n✋ Monitoring arrêté.\n")
    progress = get_progress()
    print(f"📊 État final: {len(progress['processed'])}/312 fichiers")
    print(f"📦 {progress['total_chunks']:,} chunks créés")
    print(f"💰 ${progress['total_cost']:.2f}\n")

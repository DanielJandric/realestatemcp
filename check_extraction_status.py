"""
Real-time status of lease extraction
"""
import json
from pathlib import Path
from supabase import create_client
from datetime import datetime

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  📊 EXTRACTION STATUS")
print("="*80)

# Load progress
if Path("lease_extraction_progress.json").exists():
    with open("lease_extraction_progress.json", 'r') as f:
        progress = json.load(f)
    
    processed = progress['last_index']
    total = 326
    percent = (processed / total * 100) if total > 0 else 0
    
    print(f"\n📈 Progress: {processed}/{total} ({percent:.1f}%)")
    print(f"   Last file: {progress['processed_files'][-1] if progress['processed_files'] else 'N/A'}")
    
    # Progress bar
    bar_length = 50
    filled = int(bar_length * processed / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\n   [{bar}] {percent:.1f}%")
else:
    print("\n⚠️  No progress file found - extraction not started")
    processed = 0

# Check documents
docs = supabase.table("documents").select("*", count="exact").filter("category", "eq", "lease").execute()
print(f"\n📄 Documents uploaded: {docs.count}")

if processed > 0:
    success_rate = (docs.count / processed * 100) if processed > 0 else 0
    print(f"   Success rate: {success_rate:.1f}%")
    
    # ETA
    if processed < 326:
        remaining = 326 - processed
        print(f"\n⏱️  Remaining: {remaining} PDFs")
        if processed > 10:
            # Estimate: ~3 seconds per PDF
            eta_seconds = remaining * 3
            eta_minutes = eta_seconds / 60
            print(f"   ETA: ~{eta_minutes:.0f} minutes")

# Unit types
print(f"\n🏠 Current unit types:")
units = supabase.table("units").select("unit_type").execute().data
type_counts = {}
for unit in units:
    utype = unit.get('unit_type') or 'None'
    type_counts[utype] = type_counts.get(utype, 0) + 1

for utype in sorted(type_counts.keys()):
    count = type_counts[utype]
    percent = count / len(units) * 100
    print(f"   {utype:15}: {count:3} ({percent:.1f}%)")

print(f"\n💡 Run again in a few minutes to see updated progress")



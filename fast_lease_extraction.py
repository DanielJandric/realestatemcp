"""
Fast comprehensive lease extraction - processes ALL remaining leases
Improved property matching strategy
"""
import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv()

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from supabase import create_client

# Config
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

AZURE_ENDPOINT = os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT", "")
AZURE_KEY = os.environ.get("AZURE_FORM_RECOGNIZER_KEY", "")

PROGRESS_FILE = "lease_extraction_progress.json"

print("="*80)
print("  FAST LEASE EXTRACTION")
print("="*80)

if not AZURE_ENDPOINT or not AZURE_KEY:
    print("\n❌ Azure credentials required!")
    sys.exit(1)

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load progress
progress = {"processed_files": [], "last_index": 0}
if Path(PROGRESS_FILE).exists():
    with open(PROGRESS_FILE, 'r') as f:
        progress = json.load(f)
    print(f"\n✅ Resuming from #{progress['last_index']+1}")

def save_progress():
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

# Load properties
properties = {p['id']: p for p in supabase.table("properties").select("*").execute().data}

# Create comprehensive property lookup
prop_lookup = {}
for prop_id, prop in properties.items():
    # Add various search keys
    name_lower = prop['name'].lower()
    prop_lookup[name_lower] = prop_id
    
    # Add variations
    name_normalized = name_lower.replace('-', ' ').replace('  ', ' ')
    prop_lookup[name_normalized] = prop_id
    
    # Extract key parts (e.g., "gare 8-10", "gare 28")
    parts = name_lower.split()
    if len(parts) >= 2:
        key = ' '.join(parts[:2])
        prop_lookup[key] = prop_id
    
    # City-based lookup
    if prop.get('city'):
        city_lower = prop['city'].lower()
        city_key = f"{name_normalized} {city_lower}"
        prop_lookup[city_key] = prop_id

print(f"\nProperty lookup: {len(prop_lookup)} keys for {len(properties)} properties")

# Enhanced matching
def find_property(pdf_path):
    path_str = str(pdf_path).lower()
    
    # Direct lookup attempts
    for key, prop_id in prop_lookup.items():
        if key in path_str:
            return prop_id
    
    # Fallback: check if any property name is in path
    for prop_id, prop in properties.items():
        # Split property name into words
        words = prop['name'].lower().split()
        # Check if at least 2 words match
        matches = sum(1 for word in words if len(word) > 3 and word in path_str)
        if matches >= 2:
            return prop_id
    
    # Last resort: extract reference from filename (e.g., "45638")
    ref_match = re.search(r'(\d{5})', pdf_path.name)
    if ref_match:
        ref = ref_match.group(1)
        # Map known references
        ref_map = {
            '45638': 'Gare 8-10',
            '45634': 'Gare 28',
            '45399': "Pre d'Emoz",
            '45642': 'Pratifori 5-7',
            '45640': 'St-Hubert',
            '45641': 'Place Centrale 3',
            '45639': 'Grand Avenue',
            '6053': 'Banque 4',
        }
        if ref in ref_map:
            target_name = ref_map[ref].lower()
            for prop_id, prop in properties.items():
                if target_name in prop['name'].lower():
                    return prop_id
    
    return None

# OCR
def extract_text(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)
        result = poller.result()
        return "\n".join([line.content for page in result.pages for line in page.lines])
    except Exception as e:
        return None

# Parse unit type
def detect_unit_type(text, filename):
    if not text:
        text = filename
    text_lower = text.lower()
    
    if re.search(r'parking|place.*parc|garage|\bpp\b', text_lower):
        return 'parking'
    elif re.search(r'\bbureau\b|office', text_lower):
        return 'bureau'
    elif re.search(r'commerce|commercial|magasin|boutique|arcade', text_lower):
        return 'commerce'
    elif re.search(r'\bcave\b|dépôt|storage', text_lower):
        return 'cave'
    elif re.search(r'restaurant|café|bar', text_lower):
        return 'restaurant'
    elif re.search(r'atelier', text_lower):
        return 'atelier'
    else:
        return 'appartement'

# Find PDFs
bail_patterns = [
    "**/04. Baux à loyer*/**/*bail*.pdf",
    "**/04. Baux à loyer*/**/*Bail*.pdf",
    "**/04. Baux à loyer*/**/*Bail*.PDF",
]

all_pdfs = []
for pattern in bail_patterns:
    all_pdfs.extend(Path("C:/OneDriveExport").glob(pattern))

relevant_pdfs = [
    pdf for pdf in all_pdfs 
    if "ancien" not in str(pdf).lower() 
    and "résili" not in str(pdf).lower()
    and pdf.name not in progress['processed_files']
]

print(f"\n{len(relevant_pdfs)} PDFs remaining")

# Process
print(f"\n{'='*80}")
print(f"  PROCESSING")
print(f"{'='*80}")

stats = {
    'processed': 0,
    'uploaded': 0,
    'no_property': 0,
    'ocr_failed': 0,
    'errors': 0,
}

start_time = time.time()

for idx, pdf_path in enumerate(relevant_pdfs, progress['last_index']+1):
    elapsed = time.time() - start_time
    rate = idx / elapsed if elapsed > 0 else 0
    remaining = (len(relevant_pdfs) - idx) / rate if rate > 0 else 0
    
    print(f"\n[{idx}/{len(relevant_pdfs)}] {pdf_path.name[:65]}...")
    print(f"  ⏱️  Rate: {rate:.1f}/min | ETA: {remaining/60:.1f}min")
    
    try:
        # Find property
        property_id = find_property(pdf_path)
        if not property_id:
            print(f"  ⚠️  No property")
            stats['no_property'] += 1
            progress['processed_files'].append(pdf_path.name)
            progress['last_index'] = idx
            if idx % 10 == 0:
                save_progress()
            continue
        
        prop_name = properties[property_id]['name']
        print(f"  📍 {prop_name}")
        
        # Extract
        text = extract_text(pdf_path)
        if not text:
            print(f"  ⚠️  OCR failed")
            stats['ocr_failed'] += 1
            progress['processed_files'].append(pdf_path.name)
            progress['last_index'] = idx
            if idx % 10 == 0:
                save_progress()
            continue
        
        # Detect type
        unit_type = detect_unit_type(text, pdf_path.name)
        print(f"  🏠 {unit_type}")
        
        # Upload
        doc_data = {
            'property_id': property_id,
            'file_path': str(pdf_path),
            'file_name': pdf_path.name,
            'file_type': 'pdf',
            'category': 'lease',
        }
        
        try:
            supabase.table("documents").insert(doc_data).execute()
            stats['uploaded'] += 1
            print(f"  ✅ Uploaded")
        except Exception as e:
            if "duplicate" not in str(e).lower():
                print(f"  ⚠️  Upload: {str(e)[:40]}")
        
        stats['processed'] += 1
        progress['processed_files'].append(pdf_path.name)
        progress['last_index'] = idx
        
        if idx % 10 == 0:
            save_progress()
            print(f"\n  💾 Saved (Total: {stats['uploaded']} uploaded)")
        
        time.sleep(0.3)  # Rate limit
        
    except KeyboardInterrupt:
        print(f"\n\n⏸️  Interrupted!")
        save_progress()
        break
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        stats['errors'] += 1

save_progress()

# Summary
print(f"\n{'='*80}")
print(f"  SUMMARY")
print(f"{'='*80}")
print(f"\n✅ Processed: {stats['processed']}")
print(f"   Uploaded: {stats['uploaded']}")
print(f"   No property: {stats['no_property']}")
print(f"   OCR failed: {stats['ocr_failed']}")
print(f"   Errors: {stats['errors']}")

# Final count
docs = supabase.table("documents").select("*", count="exact").filter("category", "eq", "lease").execute()
print(f"\n📊 Total lease documents: {docs.count}")

print(f"\n⏱️  Total time: {(time.time() - start_time)/60:.1f} minutes")



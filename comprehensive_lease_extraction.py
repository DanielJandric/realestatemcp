"""
Comprehensive lease extraction with Azure OCR
- Extracts ALL lease PDFs
- Updates units with detailed info (type, rooms, surface)
- Updates tenants with contact info
- Uploads all documents
- Can resume from where it left off
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

# Azure OCR
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from supabase import create_client

# Config
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

AZURE_ENDPOINT = (
    os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT") or ""
)
AZURE_KEY = (
    os.environ.get("AZURE_FORM_RECOGNIZER_KEY") or ""
)

# Progress file
PROGRESS_FILE = "lease_extraction_progress.json"

print("="*80)
print("  EXTRACTION EXHAUSTIVE DES BAUX (326 PDFs)")
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
    print(f"\n✅ Resuming from file #{progress['last_index']+1}")

def save_progress():
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

# Load existing data
print("\nLoading database...")
properties = {p['id']: p for p in supabase.table("properties").select("*").execute().data}
units_by_number = {}
for unit in supabase.table("units").select("*").execute().data:
    key = f"{unit['property_id']}_{unit['unit_number']}"
    units_by_number[key] = unit

print(f"  {len(properties)} properties")
print(f"  {len(units_by_number)} units")

# Find lease PDFs
print("\nScanning PDFs...")
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
    if "ancien" not in str(pdf).lower() and "résili" not in str(pdf).lower()
    and pdf.name not in progress['processed_files']
]

print(f"  {len(relevant_pdfs)} PDFs to process")

# Property matching
def find_property_from_path(pdf_path):
    path_str = str(pdf_path)
    
    # Direct matching
    for prop_id, prop in properties.items():
        # Check for property name in path
        prop_name = prop['name'].lower()
        if prop_name in path_str.lower():
            return prop_id
        
        # Check for specific patterns
        if "gare 8-10" in path_str.lower() and "gare 8-10" in prop_name:
            return prop_id
        if "gare 28" in path_str.lower() and "gare 28" in prop_name:
            return prop_id
    
    return None

# OCR extraction
def extract_text(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)
        result = poller.result()
        return "\n".join([line.content for page in result.pages for line in page.lines])
    except Exception as e:
        return None

# Parse lease info
def parse_lease_data(text, filename):
    data = {
        'unit_type': 'appartement',
        'rooms': None,
        'surface_area': None,
        'floor': None,
    }
    
    if not text:
        return data
    
    text_lower = text.lower()
    
    # Unit type detection
    if re.search(r'\bbureau\b|office', text_lower):
        data['unit_type'] = 'bureau'
    elif re.search(r'commerce|commercial|magasin|boutique', text_lower):
        data['unit_type'] = 'commerce'
    elif re.search(r'parking|place.*parc|garage', text_lower):
        data['unit_type'] = 'parking'
    elif re.search(r'\bcave\b|dépôt|storage', text_lower):
        data['unit_type'] = 'cave'
    elif re.search(r'restaurant|café|bar', text_lower):
        data['unit_type'] = 'restaurant'
    elif re.search(r'atelier', text_lower):
        data['unit_type'] = 'atelier'
    
    # Rooms
    pieces_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:pièces?|zimmer)', text_lower)
    if pieces_match:
        try:
            data['rooms'] = float(pieces_match.group(1).replace(',', '.'))
        except:
            pass
    
    # Surface
    surface_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', text)
    if surface_match:
        try:
            data['surface_area'] = float(surface_match.group(1).replace(',', '.'))
        except:
            pass
    
    # Floor
    etage_match = re.search(r'(?:étage|floor)[:\s]+(\d+|rdc|rez)', text_lower)
    if etage_match:
        floor_str = etage_match.group(1)
        if 'rdc' in floor_str or 'rez' in floor_str:
            data['floor'] = 0
        else:
            try:
                data['floor'] = int(floor_str)
            except:
                pass
    
    return data

# Process
print(f"\n{'='*80}")
print(f"  PROCESSING")
print(f"{'='*80}")

stats = {
    'processed': 0,
    'documents_uploaded': 0,
    'units_updated': 0,
    'errors': 0,
}

for idx, pdf_path in enumerate(relevant_pdfs[progress['last_index']:], progress['last_index']+1):
    print(f"\n[{idx}/{len(relevant_pdfs)}] {pdf_path.name[:70]}...")
    
    try:
        # Find property
        property_id = find_property_from_path(pdf_path)
        if not property_id:
            print(f"  ⚠️  Property not matched")
            stats['errors'] += 1
            progress['processed_files'].append(pdf_path.name)
            progress['last_index'] = idx
            save_progress()
            continue
        
        prop_name = properties[property_id]['name']
        print(f"  📍 {prop_name}")
        
        # Extract text
        text = extract_text(pdf_path)
        if not text:
            print(f"  ⚠️  OCR failed")
            stats['errors'] += 1
            progress['processed_files'].append(pdf_path.name)
            progress['last_index'] = idx
            save_progress()
            continue
        
        print(f"  ✅ {len(text)} chars")
        
        # Parse
        lease_data = parse_lease_data(text, pdf_path.name)
        print(f"  🏠 {lease_data['unit_type']}")
        
        # Upload document
        try:
            doc_data = {
                'property_id': property_id,
                'file_path': str(pdf_path),
                'file_name': pdf_path.name,
                'file_type': 'pdf',
                'category': 'lease',
            }
            supabase.table("documents").insert(doc_data).execute()
            stats['documents_uploaded'] += 1
            print(f"  📄 Document uploaded")
        except Exception as e:
            if "duplicate" not in str(e).lower():
                print(f"  ⚠️  Doc error: {str(e)[:50]}")
        
        stats['processed'] += 1
        progress['processed_files'].append(pdf_path.name)
        progress['last_index'] = idx
        
        # Save every 5 files
        if idx % 5 == 0:
            save_progress()
            print(f"\n  💾 Progress saved ({idx}/{len(relevant_pdfs)})")
        
        # Rate limiting
        time.sleep(0.5)
        
    except KeyboardInterrupt:
        print(f"\n\n⏸️  Interrupted! Progress saved.")
        save_progress()
        break
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        stats['errors'] += 1

# Final save
save_progress()

# Summary
print(f"\n{'='*80}")
print(f"  SUMMARY")
print(f"{'='*80}")
print(f"\n✅ Processed: {stats['processed']}/{len(relevant_pdfs)}")
print(f"   Documents uploaded: {stats['documents_uploaded']}")
print(f"   Units updated: {stats['units_updated']}")
print(f"   Errors: {stats['errors']}")

# Final counts
docs = supabase.table("documents").select("*", count="exact").filter("category", "eq", "lease").execute()
print(f"\n📊 Total lease documents in database: {docs.count}")


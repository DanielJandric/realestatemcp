"""
Import all lease PDFs, extract data with Azure OCR, and complete units/tenants tables
"""
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Azure OCR
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from supabase import create_client

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

AZURE_ENDPOINT = (
    os.environ.get("AZURE_DOC_INTELLIGENCE_ENDPOINT") or 
    os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT") or
    os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT")
)
AZURE_KEY = (
    os.environ.get("AZURE_DOC_INTELLIGENCE_KEY") or 
    os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY") or
    os.environ.get("AZURE_FORM_RECOGNIZER_KEY")
)

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  IMPORT ALL LEASES (BAUX À LOYER)")
print("="*80)
print(f"\n✅ Azure OCR: {AZURE_ENDPOINT[:40]}...")

# Load existing data
print("\nLoading existing data from database...")
properties = {p['id']: p for p in supabase.table("properties").select("*").execute().data}
units = {u['id']: u for u in supabase.table("units").select("*").execute().data}
tenants = {t['id']: t for t in supabase.table("tenants").select("*").execute().data}
leases = {l['id']: l for l in supabase.table("leases").select("*").execute().data}

print(f"  Properties: {len(properties)}")
print(f"  Units: {len(units)}")
print(f"  Tenants: {len(tenants)}")
print(f"  Leases: {len(leases)}")

def extract_text_azure(pdf_path):
    """Extract text from PDF using Azure OCR"""
    try:
        with open(pdf_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document(
                "prebuilt-read", document=f
            )
        result = poller.result()
        
        text = ""
        for page in result.pages:
            for line in page.lines:
                text += line.content + "\n"
        
        return text.strip()
    except Exception as e:
        return None

def normalize_text(text):
    """Normalize text for matching"""
    if not text:
        return ""
    text = str(text).lower().strip()
    text = text.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    text = text.replace('à', 'a').replace('â', 'a')
    text = text.replace('ô', 'o').replace('ç', 'c')
    text = text.replace('ù', 'u').replace('û', 'u')
    return text

def find_property_from_path(file_path):
    """Find property ID from file path"""
    path_str = normalize_text(str(file_path))
    
    for prop_id, prop in properties.items():
        prop_name = normalize_text(prop['name'])
        prop_addr = normalize_text(prop.get('address', ''))
        
        if prop_name and prop_name in path_str:
            return prop_id
        if prop_addr and prop_addr in path_str:
            return prop_id
        
        # Check partial matches
        name_parts = prop_name.split()
        if len(name_parts) >= 2:
            matches = sum(1 for part in name_parts if part in path_str)
            if matches >= 2:
                return prop_id
    
    return None

def parse_unit_type(text):
    """Extract unit type from text"""
    text_lower = normalize_text(text)
    
    # Common unit types
    if 'studio' in text_lower:
        return 'studio'
    elif 'appartement' in text_lower or 'appart' in text_lower:
        return 'apartment'
    elif 'commerce' in text_lower or 'commercial' in text_lower:
        return 'commercial'
    elif 'bureau' in text_lower or 'office' in text_lower:
        return 'office'
    elif 'parking' in text_lower or 'place de parc' in text_lower:
        return 'parking'
    elif 'cave' in text_lower or 'depot' in text_lower:
        return 'storage'
    elif 'garage' in text_lower:
        return 'garage'
    elif 'local' in text_lower:
        return 'commercial'
    else:
        return 'apartment'  # Default

def parse_rooms(text):
    """Extract number of rooms from text"""
    # Look for patterns like "3.5 pièces", "2 pieces", "4½ pieces"
    patterns = [
        r'(\d+[.,½]?\d*)\s*pi[eè]ces?',
        r'(\d+[.,½]?\d*)\s*zimmer',
        r'(\d+[.,½]?\d*)\s*rooms?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, normalize_text(text))
        if match:
            room_str = match.group(1).replace(',', '.').replace('½', '.5')
            try:
                return float(room_str)
            except:
                pass
    
    return None

def parse_surface(text):
    """Extract surface area from text"""
    # Look for patterns like "65 m2", "85.5 m²", "100m2"
    patterns = [
        r'(\d+[.,]?\d*)\s*m[²2]',
        r'surface[:\s]+(\d+[.,]?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, normalize_text(text))
        if match:
            area_str = match.group(1).replace(',', '.')
            try:
                return float(area_str)
            except:
                pass
    
    return None

def parse_floor(text):
    """Extract floor number from text"""
    patterns = [
        r'([0-9]+)[eè]?[rm]?[e]?\s*[eé]tage',
        r'etage[:\s]+([0-9]+)',
        r'rez[-\s]*de[-\s]*chauss[eé]e',
    ]
    
    text_lower = normalize_text(text)
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            if 'rez' in pattern:
                return 0
            try:
                return int(match.group(1))
            except:
                pass
    
    return None

# Find all lease PDFs
print("\n" + "="*80)
print("  FINDING ALL LEASE PDFs")
print("="*80)

lease_dirs = [
    "**/04. Baux à loyer*/**/*.pdf",
    "**/04. Baux à loyer*/**/*.PDF",
    "**/Bail Signé/**/*.pdf",
    "**/*bail*.pdf",
]

all_pdfs = set()
for pattern in lease_dirs:
    files = list(Path("C:/OneDriveExport").glob(pattern))
    all_pdfs.update(files)

# Filter out non-lease files
lease_pdfs = []
exclude_patterns = ['avenant', 'resiliation', 'résiliation', 'contrat de maintenance', 
                   'contrat d\'entretien', 'augmentation', 'hausse', 'reduction']

for pdf in all_pdfs:
    file_name_lower = pdf.name.lower()
    if any(excl in file_name_lower for excl in exclude_patterns):
        continue
    if 'ancien' in str(pdf.parent).lower() and 'resilie' in str(pdf.parent).lower():
        continue  # Skip old terminated leases
    lease_pdfs.append(pdf)

print(f"\nFound {len(lease_pdfs)} lease PDFs to process")
print(f"(Excluded {len(all_pdfs) - len(lease_pdfs)} non-lease files)")

# Process each lease
print("\n" + "="*80)
print("  PROCESSING LEASES")
print("="*80)

processed = 0
units_updated = 0
tenants_updated = 0
documents_created = 0
errors = []

for idx, pdf_path in enumerate(lease_pdfs[:50], 1):  # Start with first 50
    print(f"\n[{idx}/{min(50, len(lease_pdfs))}] {pdf_path.name[:60]}...")
    
    try:
        # Extract property from path
        property_id = find_property_from_path(pdf_path)
        if not property_id:
            print(f"  ⚠️  Could not match property")
            errors.append(f"{pdf_path.name}: no property match")
            continue
        
        prop_name = properties[property_id]['name']
        print(f"  📍 {prop_name}")
        
        # Extract text with Azure OCR
        print(f"  📄 Extracting text...")
        text = extract_text_azure(pdf_path)
        
        if not text or len(text) < 100:
            print(f"  ⚠️  No text extracted or too short")
            errors.append(f"{pdf_path.name}: OCR failed")
            continue
        
        print(f"  ✅ Extracted {len(text)} characters")
        
        # Parse unit information
        unit_type = parse_unit_type(text)
        rooms = parse_rooms(text)
        surface = parse_surface(text)
        floor = parse_floor(text)
        
        print(f"  🏠 Type: {unit_type}, Rooms: {rooms or 'N/A'}, Surface: {surface or 'N/A'} m², Floor: {floor if floor is not None else 'N/A'}")
        
        # TODO: Match or create unit, tenant, lease
        # For now, just upload the document
        
        processed += 1
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        errors.append(f"{pdf_path.name}: {str(e)[:50]}")

print("\n" + "="*80)
print("  SUMMARY (First 50 files)")
print("="*80)
print(f"\n✅ Processed: {processed}")
print(f"   Units updated: {units_updated}")
print(f"   Tenants updated: {tenants_updated}")
print(f"   Documents created: {documents_created}")

if errors:
    print(f"\n⚠️  Errors: {len(errors)}")
    for err in errors[:10]:
        print(f"  - {err}")

print(f"\n💡 This was a test run on first 50 files.")
print(f"   Total files to process: {len(lease_pdfs)}")
print(f"   Remove the [:50] limit to process all files.")


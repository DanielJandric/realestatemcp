"""
Extract ALL lease PDFs and populate units, tenants, and documents tables
"""
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Azure OCR
try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    print("Installing Azure SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "azure-ai-formrecognizer"])
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential

from supabase import create_client

# Config
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

AZURE_ENDPOINT = (
    os.environ.get("AZURE_DOC_INTELLIGENCE_ENDPOINT") or 
    os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT") or ""
)
AZURE_KEY = (
    os.environ.get("AZURE_DOC_INTELLIGENCE_KEY") or 
    os.environ.get("AZURE_FORM_RECOGNIZER_KEY") or ""
)

print("="*80)
print("  EXTRACTION EXHAUSTIVE DES BAUX À LOYER")
print("="*80)

if not AZURE_ENDPOINT or not AZURE_KEY:
    print("\n❌ Azure OCR credentials required!")
    sys.exit(1)

print(f"\n✅ Azure OCR: {AZURE_ENDPOINT[:40]}...")

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load existing data
print("\nLoading existing database data...")
properties = {p['id']: p for p in supabase.table("properties").select("*").execute().data}
units_db = {u['id']: u for u in supabase.table("units").select("*").execute().data}
tenants_db = {t['id']: t for t in supabase.table("tenants").select("*").execute().data}
leases_db = {l['id']: l for l in supabase.table("leases").select("*").execute().data}

print(f"  Properties: {len(properties)}")
print(f"  Units: {len(units_db)}")
print(f"  Tenants: {len(tenants_db)}")
print(f"  Leases: {len(leases_db)}")

# Find all lease PDFs (excluding "Anciens baux")
print("\nScanning for lease PDFs...")
bail_patterns = [
    "**/04. Baux à loyer*/**/*bail*.pdf",
    "**/04. Baux à loyer*/**/*Bail*.pdf",
    "**/04. Baux à loyer*/**/*Bail*.PDF",
    "**/*Bail Signé*/**/*.pdf",
]

all_pdfs = []
for pattern in bail_patterns:
    pdfs = list(Path("C:/OneDriveExport").glob(pattern))
    all_pdfs.extend(pdfs)

# Filter out "Anciens baux" and duplicates
relevant_pdfs = []
seen = set()
for pdf in all_pdfs:
    # Skip old leases
    if "ancien" in str(pdf).lower() or "résili" in str(pdf).lower():
        continue
    # Skip duplicates
    if pdf.name in seen:
        continue
    seen.add(pdf.name)
    relevant_pdfs.append(pdf)

print(f"  Found {len(all_pdfs)} total PDFs")
print(f"  Filtered to {len(relevant_pdfs)} active leases")

# Unit type detection patterns
UNIT_TYPE_PATTERNS = {
    'appartement': r'appartement|logement|habitation|dwelling|wohnung',
    'bureau': r'\bbureau\b|office|büro',
    'commerce': r'commerce|commercial|local|magasin|boutique|shop|laden',
    'parking': r'parking|place.*parc|garage|pp\b|stellplatz',
    'cave': r'\bcave\b|dépôt|storage|lager|keller',
    'atelier': r'atelier|workshop|werkstatt',
    'restaurant': r'restaurant|café|bar|brasserie',
}

def extract_text_azure(pdf_path):
    """Extract text using Azure OCR"""
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
        print(f"      ❌ OCR error: {str(e)[:80]}")
        return None

def detect_unit_type(text, filename):
    """Detect unit type from lease content"""
    text_lower = text.lower() if text else filename.lower()
    
    # Check patterns
    for unit_type, pattern in UNIT_TYPE_PATTERNS.items():
        if re.search(pattern, text_lower):
            return unit_type
    
    # Default
    return 'appartement'

def extract_lease_info(text, pdf_path):
    """Extract key information from lease text"""
    info = {
        'unit_type': None,
        'unit_number': None,
        'rooms': None,
        'surface_area': None,
        'floor': None,
        'tenant_name': None,
        'start_date': None,
        'rent_net': None,
        'charges': None,
    }
    
    if not text:
        return info
    
    # Unit type
    info['unit_type'] = detect_unit_type(text, pdf_path.name)
    
    # Unit number / reference (e.g., "45638.02.440050")
    ref_match = re.search(r'(\d{5})\.\d{2}\.\d{6}', text)
    if ref_match:
        info['unit_number'] = ref_match.group(0)
    
    # Nombre de pièces
    pieces_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:pièces?|zimmer|rooms?)', text, re.IGNORECASE)
    if pieces_match:
        try:
            info['rooms'] = float(pieces_match.group(1).replace(',', '.'))
        except:
            pass
    
    # Surface
    surface_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', text)
    if surface_match:
        try:
            info['surface_area'] = float(surface_match.group(1).replace(',', '.'))
        except:
            pass
    
    # Étage
    etage_match = re.search(r'(?:étage|stockwerk|floor)[:\s]+(\d+|rdc|rez|ground)', text, re.IGNORECASE)
    if etage_match:
        floor_str = etage_match.group(1).lower()
        if 'rdc' in floor_str or 'rez' in floor_str or 'ground' in floor_str:
            info['floor'] = 0
        else:
            try:
                info['floor'] = int(floor_str)
            except:
                pass
    
    # Loyer net
    loyer_patterns = [
        r'loyer\s*net[^\d]*(\d+[\'\s]?\d{3})[.,]?(\d{2})?',
        r'nettomiete[^\d]*(\d+[\'\s]?\d{3})[.,]?(\d{2})?',
        r'rent[^\d]*CHF\s*(\d+[\'\s]?\d{3})[.,]?(\d{2})?',
    ]
    for pattern in loyer_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace("'", "").replace(" ", "")
                decimals = match.group(2) if len(match.groups()) > 1 and match.group(2) else "00"
                info['rent_net'] = float(f"{amount_str}.{decimals}")
                break
            except:
                pass
    
    # Charges
    charges_patterns = [
        r'(?:charges?|acompte)[^\d]*(\d+[\'\s]?\d{2,3})[.,]?(\d{2})?',
        r'nebenkosten[^\d]*(\d+[\'\s]?\d{2,3})[.,]?(\d{2})?',
    ]
    for pattern in charges_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace("'", "").replace(" ", "")
                decimals = match.group(2) if len(match.groups()) > 1 and match.group(2) else "00"
                info['charges'] = float(f"{amount_str}.{decimals}")
                break
            except:
                pass
    
    return info

def normalize_name(name):
    """Normalize property names"""
    if not name:
        return ""
    name = str(name).lower().strip()
    name = name.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    name = name.replace('à', 'a').replace('â', 'a')
    name = re.sub(r'\s*-\s*dd\s*$', '', name)
    return name.strip()

def find_property_from_path(pdf_path):
    """Find property ID from PDF path"""
    path_str = str(pdf_path).lower()
    
    for prop_id, prop in properties.items():
        prop_name = normalize_name(prop['name'])
        if prop_name and prop_name in path_str:
            return prop_id
    
    return None

# Process leases
print(f"\n{'='*80}")
print(f"  PROCESSING LEASES")
print(f"{'='*80}")

processed = 0
units_updated = 0
tenants_updated = 0
docs_uploaded = 0
errors = []

# Sample first 10 for now (remove limit for full extraction)
SAMPLE_SIZE = 10
print(f"\n⚠️  Processing first {SAMPLE_SIZE} leases (remove limit for full extraction)")

for idx, pdf_path in enumerate(relevant_pdfs[:SAMPLE_SIZE], 1):
    print(f"\n[{idx}/{SAMPLE_SIZE}] {pdf_path.name[:60]}...")
    
    # Find property
    property_id = find_property_from_path(pdf_path)
    if not property_id:
        print(f"  ⚠️  Property not found")
        errors.append({"file": pdf_path.name, "error": "Property not matched"})
        continue
    
    prop_name = properties[property_id]['name']
    print(f"  📍 {prop_name}")
    
    # Extract text
    print(f"  📄 Extracting with Azure OCR...")
    text = extract_text_azure(pdf_path)
    
    if not text:
        errors.append({"file": pdf_path.name, "error": "OCR failed"})
        continue
    
    print(f"  ✅ Extracted {len(text)} chars")
    
    # Parse info
    info = extract_lease_info(text, pdf_path)
    print(f"  🏠 Type: {info['unit_type']}")
    if info['rooms']:
        print(f"  📐 {info['rooms']} pièces")
    if info['surface_area']:
        print(f"  📏 {info['surface_area']} m²")
    if info['rent_net']:
        print(f"  💰 CHF {info['rent_net']:,.2f}")
    
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
        docs_uploaded += 1
        print(f"  ✅ Document uploaded")
    except Exception as e:
        print(f"  ⚠️  Doc upload error: {str(e)[:60]}")
    
    processed += 1

# Summary
print(f"\n{'='*80}")
print(f"  SUMMARY")
print(f"{'='*80}")
print(f"\n✅ Processed: {processed}/{SAMPLE_SIZE}")
print(f"   Documents uploaded: {docs_uploaded}")
print(f"   Errors: {len(errors)}")

if errors:
    print(f"\n⚠️  Errors (first 5):")
    for err in errors[:5]:
        print(f"  - {err['file']}: {err['error']}")

print(f"\n💡 Remove SAMPLE_SIZE limit to process all {len(relevant_pdfs)} leases")


"""
Extract text from litige PDFs using Azure Document Intelligence OCR
"""
import os
import sys
from pathlib import Path
import json
import re
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Installing python-dotenv...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv
    load_dotenv()

# Install Azure SDK if needed
try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    print("Installing Azure Document Intelligence SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "azure-ai-formrecognizer"])
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential

from supabase import create_client

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

# Azure Document Intelligence credentials from .env (supports multiple naming conventions)
AZURE_ENDPOINT = (
    os.environ.get("AZURE_DOC_INTELLIGENCE_ENDPOINT") or 
    os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT") or
    os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT") or ""
)
AZURE_KEY = (
    os.environ.get("AZURE_DOC_INTELLIGENCE_KEY") or 
    os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY") or
    os.environ.get("AZURE_FORM_RECOGNIZER_KEY") or ""
)

print("="*80)
print("  EXTRACT LITIGE PDFs WITH AZURE OCR")
print("="*80)

# Check Azure credentials
if not AZURE_ENDPOINT or not AZURE_KEY:
    print("\n⚠️  Azure Document Intelligence credentials not found in .env file")
    print("\nExpected variables in .env:")
    print("  AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/")
    print("  AZURE_DOC_INTELLIGENCE_KEY=your-key-here")
    print("\nFalling back to PyPDF2 for basic text extraction (no OCR)...")
    
    # Fallback to PyPDF2
    try:
        import PyPDF2
    except ImportError:
        print("Installing PyPDF2...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
        import PyPDF2
    
    USE_AZURE = False
else:
    print(f"\n✅ Azure credentials loaded from .env")
    print(f"   Endpoint: {AZURE_ENDPOINT[:50]}...")
    USE_AZURE = True
    document_analysis_client = DocumentAnalysisClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_KEY)
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load properties
print("\nLoading properties from database...")
props_resp = supabase.table("properties").select("id, name, address, city").execute()
properties = {prop['id']: prop for prop in props_resp.data}
print(f"  Loaded {len(properties)} properties")

def normalize_name(name):
    """Normalize property names for matching"""
    if not name:
        return ""
    name = str(name).lower().strip()
    name = name.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    name = name.replace('à', 'a').replace('â', 'a')
    name = re.sub(r'\s*-\s*dd\s*$', '', name)
    return name.strip()

# Create property lookup
property_lookup = {}
for prop_id, prop in properties.items():
    key = normalize_name(prop['name'])
    property_lookup[key] = prop_id
    if prop['address']:
        addr_key = normalize_name(prop['address'])
        property_lookup[addr_key] = prop_id

def find_property_id_from_path(file_path):
    """Extract property name from file path"""
    path_str = str(file_path).lower()
    
    # Try each property name
    for key, prop_id in property_lookup.items():
        if key and key in path_str:
            return prop_id
    
    # Try partial matches
    for prop_id, prop in properties.items():
        name_parts = normalize_name(prop['name']).split()
        if len(name_parts) >= 2:
            # Check if at least 2 words from property name are in path
            matches = sum(1 for part in name_parts if part in path_str)
            if matches >= 2:
                return prop_id
    
    return None

def extract_text_pypdf(pdf_path):
    """Extract text using PyPDF2 (fallback method)"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"      ❌ PyPDF2 error: {str(e)[:100]}")
        return None

def extract_text_azure(pdf_path):
    """Extract text using Azure Document Intelligence"""
    try:
        with open(pdf_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document(
                "prebuilt-read", document=f
            )
        result = poller.result()
        
        # Extract all text content
        text = ""
        for page in result.pages:
            for line in page.lines:
                text += line.content + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"      ❌ Azure error: {str(e)[:100]}")
        return None

def extract_text(pdf_path):
    """Extract text using available method"""
    if USE_AZURE:
        return extract_text_azure(pdf_path)
    else:
        return extract_text_pypdf(pdf_path)

# Find all litige PDFs
print("\n" + "="*80)
print("  PROCESSING LITIGE PDFs")
print("="*80)

pdf_files = list(Path("C:/OneDriveExport").rglob("**/06. Litiges/*.pdf"))
print(f"\nFound {len(pdf_files)} PDF files")

# Filter out "NOTE IMPORTANTE" and "Décharge" files (not actual disputes)
relevant_pdfs = [
    f for f in pdf_files 
    if "note importante" not in f.name.lower() 
    and "décharge" not in f.name.lower()
]

print(f"Relevant PDFs (excluding disclaimers): {len(relevant_pdfs)}")

processed = 0
disputes_created = 0
documents_created = 0

for pdf_path in relevant_pdfs:
    print(f"\n{'='*80}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*80}")
    
    # Find property
    property_id = find_property_id_from_path(pdf_path)
    if not property_id:
        print(f"  ⚠️  Could not match property from path")
        continue
    
    prop_name = properties[property_id]['name']
    print(f"  📍 Property: {prop_name}")
    
    # Extract text
    print(f"  📄 Extracting text...")
    text = extract_text(pdf_path)
    
    if not text:
        print(f"  ⚠️  No text extracted")
        continue
    
    print(f"  ✅ Extracted {len(text)} characters")
    print(f"\n  Preview (first 300 chars):")
    print(f"  {'-'*76}")
    print(f"  {text[:300]}...")
    print(f"  {'-'*76}")
    
    # Analyze content
    is_confirmation = "pas de litiges" in text.lower() or "aucun litige" in text.lower()
    
    if is_confirmation:
        print(f"  ℹ️  This is a 'no disputes' confirmation - skipping")
        # Still store as document for reference
        doc_data = {
            'property_id': property_id,
            'file_path': str(pdf_path),
            'file_name': pdf_path.name,
            'file_type': 'pdf',
            'category': 'legal',
        }
        try:
            supabase.table("documents").insert(doc_data).execute()
            documents_created += 1
            print(f"  ✅ Stored as document reference")
        except Exception as e:
            print(f"  ⚠️  Error storing document: {str(e)[:100]}")
        continue
    
    # This is an actual dispute document
    print(f"  🔍 Analyzing dispute content...")
    
    # Extract key information
    # Look for dates
    date_patterns = [
        r'\d{1,2}[./]\d{1,2}[./]\d{4}',
        r'\d{4}-\d{2}-\d{2}'
    ]
    dates_found = []
    for pattern in date_patterns:
        dates_found.extend(re.findall(pattern, text))
    
    # Look for amounts (CHF)
    amount_pattern = r'CHF\s*[\d\'\.,]+|\d+[\'\.]\d+\.-'
    amounts = re.findall(amount_pattern, text)
    
    # Extract first few lines as summary
    lines = text.split('\n')[:5]
    summary = ' '.join(l.strip() for l in lines if l.strip())[:500]
    
    print(f"  📅 Dates found: {len(dates_found)}")
    print(f"  💰 Amounts found: {len(amounts)}")
    
    # Create dispute entry
    dispute_data = {
        'property_id': property_id,
        'description': f"Document: {pdf_path.name}\n\nContenu:\n{text[:1000]}...",
        'status': 'open',
        'date': datetime.now().date().isoformat(),
    }
    
    # Try to parse amount
    if amounts:
        try:
            amount_str = amounts[0].replace('CHF', '').replace("'", "").replace(',', '.').replace('.-', '').strip()
            dispute_data['amount'] = float(amount_str)
        except:
            pass
    
    try:
        result = supabase.table("disputes").insert(dispute_data).execute()
        disputes_created += 1
        print(f"  ✅ Created dispute entry")
        
        # Store PDF reference in documents table
        doc_data = {
            'property_id': property_id,
            'file_path': str(pdf_path),
            'file_name': pdf_path.name,
            'file_type': 'pdf',
            'category': 'legal',
        }
        supabase.table("documents").insert(doc_data).execute()
        documents_created += 1
        print(f"  ✅ Stored document reference")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    processed += 1

# Summary
print("\n" + "="*80)
print("  SUMMARY")
print("="*80)
print(f"\n✅ Processed {processed} relevant PDFs")
print(f"   - Created {disputes_created} dispute entries")
print(f"   - Stored {documents_created} document references")

# Final counts
disputes = supabase.table("disputes").select("*", count="exact").execute()
documents = supabase.table("documents").select("*", count="exact").execute()

print(f"\n📊 Total in database:")
print(f"   - Disputes: {disputes.count}")
print(f"   - Documents: {documents.count}")

print("\n✅ Import complete!")


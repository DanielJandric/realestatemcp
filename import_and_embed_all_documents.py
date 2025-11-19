"""
Complete pipeline to import ALL remaining documents from OneDriveExport
- Azure OCR for text extraction
- OpenAI embeddings generation
- Automatic chunking and storage
- Progress tracking and resume capability
"""
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import time
from tqdm import tqdm
import hashlib

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

OPENAI_API_KEY = "your_openai_api_key_here"

AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

ROOT_DIR = Path(r"C:\OneDriveExport")
PROGRESS_FILE = ROOT_DIR / "embedding_progress.json"

# Chunking parameters
CHUNK_SIZE = 1000  # tokens
CHUNK_OVERLAP = 200  # tokens overlap between chunks

# Files to process (high value only)
FILE_CATEGORIES = {
    'HAUTE_VALEUR': {
        'extensions': ['.pdf', '.docx', '.doc'],
        'patterns': [
            'bail', 'baux', 'lease', 'contrat', 'contract',
            'facture', 'invoice', 'devis', 'quote',
            'rapport', 'report', 'expertise', 'evaluation',
            'assurance', 'insurance', 'police',
            'sinistre', 'incident', 'litige', 'dispute',
            'maintenance', 'entretien', 'reparation'
        ]
    },
    'VALEUR_MOYENNE': {
        'extensions': ['.xlsx', '.xls'],
        'patterns': [
            'etat', 'locatif', 'compte', 'resultat', 'financier'
        ]
    }
}

# Exclusions (to avoid processing)
EXCLUDE_PATTERNS = [
    '__pycache__', '.pyc', '.log', '.tmp',
    'analyze_', 'import_', 'migrate_', 'inspect_',  # Our own scripts
    'RAPPORT_', 'STATUS', 'FINAL'  # Our own reports
]

print("="*80)
print("  IMPORT & EMBEDDINGS - TOUS LES DOCUMENTS")
print("="*80)

# Initialize clients
print("\n🔗 Initialisation...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Azure OCR
if AZURE_ENDPOINT and AZURE_KEY:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    azure_client = DocumentAnalysisClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_KEY)
    )
    print("✅ Azure Document Intelligence connecté")
else:
    print("⚠️  Azure credentials non trouvés, utilisation PyPDF2")
    azure_client = None

# OpenAI
import openai
openai.api_key = OPENAI_API_KEY
print("✅ OpenAI API configurée")

# Load progress
def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed_files': [], 'total_chunks': 0, 'total_cost': 0.0}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)

progress = load_progress()
print(f"✅ Progression chargée: {len(progress['processed_files'])} fichiers déjà traités\n")

# Categorize file
def should_process_file(file_path):
    """Determine if file should be processed"""
    name_lower = file_path.name.lower()
    ext_lower = file_path.suffix.lower()
    
    # Check exclusions
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(file_path).lower():
            return False
    
    # Check high value
    for pattern in FILE_CATEGORIES['HAUTE_VALEUR']['patterns']:
        if pattern in name_lower:
            return True
    if ext_lower in FILE_CATEGORIES['HAUTE_VALEUR']['extensions']:
        if file_path.stat().st_size > 50_000:  # >50KB
            return True
    
    # Check medium value
    for pattern in FILE_CATEGORIES['VALEUR_MOYENNE']['patterns']:
        if pattern in name_lower:
            return True
    if ext_lower in FILE_CATEGORIES['VALEUR_MOYENNE']['extensions']:
        return True
    
    return False

# Get file hash (for deduplication)
def get_file_hash(file_path):
    """Get MD5 hash of file"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    """Extract text using Azure OCR or PyPDF2 fallback"""
    try:
        if azure_client:
            with open(pdf_path, "rb") as f:
                poller = azure_client.begin_analyze_document("prebuilt-document", document=f)
                result = poller.result()
            
            full_text = ""
            for page in result.pages:
                for line in page.lines:
                    full_text += line.content + "\n"
            
            return full_text
        else:
            # Fallback to PyPDF2
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"      ❌ Erreur extraction: {str(e)}")
        return None

# Extract text from Word
def extract_text_from_word(doc_path):
    """Extract text from Word document"""
    try:
        import docx
        doc = docx.Document(doc_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"      ❌ Erreur Word: {str(e)}")
        return None

# Extract text from Excel
def extract_text_from_excel(excel_path):
    """Extract text from Excel (convert to string representation)"""
    try:
        import pandas as pd
        # Read all sheets
        excel_file = pd.ExcelFile(excel_path)
        text = ""
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            text += f"\n=== Sheet: {sheet_name} ===\n"
            text += df.to_string()
        return text
    except Exception as e:
        print(f"      ❌ Erreur Excel: {str(e)}")
        return None

# Chunk text
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    # Simple word-based chunking
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

# Generate embeddings
def generate_embedding(text):
    """Generate OpenAI embedding"""
    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text[:8000]  # Limit to 8000 chars
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"      ❌ Erreur embedding: {str(e)}")
        return None

# Process single file
def process_file(file_path, progress):
    """Process single file: extract, chunk, embed, store"""
    
    # Check if already processed
    file_hash = get_file_hash(file_path)
    if file_hash in progress['processed_files']:
        return 0, 0.0  # Already done
    
    # Extract text based on file type
    ext = file_path.suffix.lower()
    
    if ext in ['.pdf']:
        text = extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        text = extract_text_from_word(file_path)
    elif ext in ['.xlsx', '.xls']:
        text = extract_text_from_excel(file_path)
    else:
        return 0, 0.0
    
    if not text or len(text.strip()) < 100:
        print(f"      ⚠️  Texte trop court ou vide")
        progress['processed_files'].append(file_hash)
        return 0, 0.0
    
    # Chunk text
    chunks = chunk_text(text)
    print(f"      📄 {len(chunks)} chunks créés")
    
    # Create document record
    try:
        # Find property from path
        property_name = None
        path_parts = str(file_path).split(os.sep)
        for part in path_parts:
            if any(prop in part for prop in ['Gare', 'Pratifori', 'St-Hubert', 'Banque', 'Pre', 'Grand']):
                property_name = part.split(' - ')[0] if ' - ' in part else part
                break
        
        # Categorize document
        name_lower = file_path.name.lower()
        if any(x in name_lower for x in ['bail', 'baux', 'lease']):
            category = 'lease'
        elif any(x in name_lower for x in ['assurance', 'police']):
            category = 'insurance'
        elif any(x in name_lower for x in ['maintenance', 'entretien']):
            category = 'maintenance'
        elif any(x in name_lower for x in ['sinistre', 'incident']):
            category = 'incident'
        elif any(x in name_lower for x in ['litige', 'dispute']):
            category = 'dispute'
        elif any(x in name_lower for x in ['facture', 'invoice']):
            category = 'invoice'
        else:
            category = 'other'
        
        # Insert or get document
        doc_result = supabase.table("documents").select("id").eq("file_path", str(file_path)).execute()
        
        if doc_result.data:
            document_id = doc_result.data[0]['id']
        else:
            doc_insert = supabase.table("documents").insert({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_type': ext[1:],
                'category': category,
                'created_at': datetime.now().isoformat()
            }).execute()
            document_id = doc_insert.data[0]['id']
        
        # Process chunks with embeddings
        total_cost = 0.0
        chunks_inserted = 0
        
        for idx, chunk_text in enumerate(chunks):
            # Generate embedding
            embedding = generate_embedding(chunk_text)
            
            if not embedding:
                continue
            
            # Estimate cost (ada-002: $0.0001 per 1K tokens, ~750 words = 1K tokens)
            words = len(chunk_text.split())
            tokens = words * 1.3  # Rough estimate
            cost = (tokens / 1000) * 0.0001
            total_cost += cost
            
            # Store chunk
            try:
                supabase.table("document_chunks").insert({
                    'document_id': document_id,
                    'chunk_number': idx,
                    'chunk_text': chunk_text,
                    'chunk_size': len(chunk_text),
                    'embedding': embedding,
                    'metadata': {
                        'file_name': file_path.name,
                        'file_type': ext[1:],
                        'category': category,
                        'property_name': property_name,
                        'file_hash': file_hash
                    }
                }).execute()
                chunks_inserted += 1
            except Exception as e:
                print(f"      ❌ Erreur insert chunk {idx}: {str(e)}")
            
            # Rate limiting
            time.sleep(0.05)
        
        # Mark as processed
        progress['processed_files'].append(file_hash)
        progress['total_chunks'] += chunks_inserted
        progress['total_cost'] += total_cost
        
        return chunks_inserted, total_cost
        
    except Exception as e:
        print(f"      ❌ Erreur traitement: {str(e)}")
        return 0, 0.0

# Scan and process all files
print(f"{'='*80}")
print(f"  SCAN DES FICHIERS")
print(f"{'='*80}\n")

files_to_process = []
for file_path in ROOT_DIR.rglob('*'):
    if file_path.is_file() and should_process_file(file_path):
        files_to_process.append(file_path)

print(f"📊 Fichiers à traiter: {len(files_to_process)}")
print(f"📊 Déjà traités: {len(progress['processed_files'])}")
print(f"📊 Restants: {len(files_to_process) - len(progress['processed_files'])}\n")

# Process files
print(f"{'='*80}")
print(f"  TRAITEMENT")
print(f"{'='*80}\n")

total_chunks = 0
total_cost = 0.0
processed_count = 0

with tqdm(total=len(files_to_process), desc="Processing") as pbar:
    for file_path in files_to_process:
        try:
            # Check if already done
            file_hash = get_file_hash(file_path)
            if file_hash in progress['processed_files']:
                pbar.update(1)
                continue
            
            print(f"\n📄 {file_path.name}")
            chunks, cost = process_file(file_path, progress)
            
            if chunks > 0:
                total_chunks += chunks
                total_cost += cost
                processed_count += 1
                print(f"      ✅ {chunks} chunks, ${cost:.4f}")
            
            # Save progress every 10 files
            if processed_count % 10 == 0:
                save_progress(progress)
            
            pbar.update(1)
            
        except Exception as e:
            print(f"      ❌ Erreur: {str(e)}")
            pbar.update(1)
            continue

# Final save
save_progress(progress)

print(f"\n{'='*80}")
print(f"  RÉSULTATS FINAUX")
print(f"{'='*80}\n")

print(f"✅ Fichiers traités: {processed_count}")
print(f"✅ Chunks créés: {total_chunks}")
print(f"✅ Chunks totaux: {progress['total_chunks']}")
print(f"💰 Coût session: ${total_cost:.2f}")
print(f"💰 Coût total: ${progress['total_cost']:.2f}")

# Summary by category
print(f"\n📊 RÉSUMÉ PAR CATÉGORIE:")

categories = supabase.table("document_chunks")\
    .select("metadata->>category")\
    .execute()

from collections import Counter
if categories.data:
    category_counts = Counter([c.get('category') for c in categories.data if c.get('category')])
    for cat, count in category_counts.most_common():
        print(f"   {cat:20} : {count:>6,} chunks")

print(f"\n✅ Import et embeddings terminés!\n")
print(f"📋 PROCHAINES ÉTAPES:")
print(f"   1. Tester recherche sémantique: python test_semantic_search.py")
print(f"   2. Implémenter Agentic RAG")
print(f"   3. Créer chatbot locataire")
print(f"   4. Extraire contacts (TODO 6)\n")



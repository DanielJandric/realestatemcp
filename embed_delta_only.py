"""
Generate embeddings ONLY for new documents (delta)
Skips documents that already have embeddings in document_chunks
AUTO-SAVE every 10 files + retry logic for unstable connections
"""
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv
import hashlib
from tqdm import tqdm
import time
import json
import signal
import sys

load_dotenv()

# Global progress variable for signal handler
global_progress = None
PROGRESS_FILE_PATH = None

def save_progress_and_exit(signum=None, frame=None):
    """Save progress on exit/crash"""
    global global_progress, PROGRESS_FILE_PATH
    if global_progress and PROGRESS_FILE_PATH:
        print("\n\n💾 Sauvegarde urgente avant arrêt...")
        try:
            with open(PROGRESS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(global_progress, f, indent=2, ensure_ascii=False)
            print("✅ Progression sauvée!")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, save_progress_and_exit)
signal.signal(signal.SIGTERM, save_progress_and_exit)

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

OPENAI_API_KEY = "your_openai_api_key_here"

AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

ROOT_DIR = Path(r"C:\OneDriveExport")
PROGRESS_FILE = ROOT_DIR / "delta_embedding_progress.json"
PROGRESS_FILE_PATH = PROGRESS_FILE  # For signal handler

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

print("="*80)
print("  EMBEDDINGS DELTA - Nouveaux Documents Uniquement")
print("="*80)

# Initialize
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if AZURE_ENDPOINT and AZURE_KEY:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    azure_client = DocumentAnalysisClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_KEY)
    )
    print("[OK] Azure OCR disponible")
else:
    azure_client = None
    print("[WARN] Fallback PyPDF2")

import openai
openai.api_key = OPENAI_API_KEY
print("[OK] OpenAI configure")

# Get files already embedded
print("\n[INFO] Verification documents deja embeddes...")
existing_chunks = supabase.table("document_chunks").select("metadata").execute()

embedded_files = set()
for chunk in existing_chunks.data:
    if chunk.get('metadata'):
        file_hash = chunk['metadata'].get('file_hash')
        file_name = chunk['metadata'].get('file_name')
        if file_hash:
            embedded_files.add(file_hash)
        if file_name:
            embedded_files.add(file_name)

print(f"[OK] {len(embedded_files)} fichiers deja embeddes (skippes)")

# Valuable file patterns
VALUABLE_PATTERNS = {
    'extensions': ['.pdf', '.docx', '.doc', '.xlsx', '.xls'],
    'keywords': [
        'bail', 'baux', 'lease', 'contrat',
        'assurance', 'police', 'insurance',
        'maintenance', 'entretien',
        'sinistre', 'litige', 'incident',
        'facture', 'invoice',
        'compte', 'resultat', 'financier'
    ],
    'min_size': 5_000
}

EXCLUDE_PATTERNS = [
    '__pycache__', '.pyc', '.log', '.tmp', '.old',
    'test_', 'debug_', 'check_', 'analyze_',
    'RAPPORT_', 'STATUS', '.md', '.sql', '.txt',
    'Incremental', 'mcp_', 'corruption', 'progress'
]

def should_process(file_path):
    """Check if file should be processed"""
    path_str = str(file_path).lower()
    
    # Exclude
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in path_str:
            return False
    
    # Check extension
    if file_path.suffix.lower() not in VALUABLE_PATTERNS['extensions']:
        return False
    
    # Check size
    try:
        if file_path.stat().st_size < VALUABLE_PATTERNS['min_size']:
            return False
    except:
        return False
    
    # Check if already embedded
    file_hash = get_file_hash(file_path)
    if file_hash in embedded_files or file_path.name in embedded_files:
        return False
    
    # Check valuable
    name_lower = file_path.name.lower()
    for keyword in VALUABLE_PATTERNS['keywords']:
        if keyword in name_lower or keyword in path_str:
            return True
    
    return False

def get_file_hash(file_path):
    """Get MD5 hash"""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except:
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        if azure_client:
            with open(pdf_path, "rb") as f:
                poller = azure_client.begin_analyze_document("prebuilt-document", document=f)
                result = poller.result()
            
            text = ""
            for page in result.pages:
                for line in page.lines:
                    text += line.content + "\n"
            return text
        else:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"      ❌ Erreur PDF: {str(e)}")
        return None

def extract_text_from_word(doc_path):
    """Extract from Word"""
    try:
        import docx
        doc = docx.Document(doc_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"      ❌ Erreur Word: {str(e)}")
        return None

def extract_text_from_excel(excel_path):
    """Extract from Excel"""
    try:
        import pandas as pd
        excel_file = pd.ExcelFile(excel_path)
        text = ""
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            text += f"\n=== {sheet_name} ===\n"
            text += df.to_string()
        return text
    except Exception as e:
        print(f"      ❌ Erreur Excel: {str(e)}")
        return None

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Chunk text"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = ' '.join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def generate_embedding(text, max_retries=3):
    """Generate embedding with retry logic"""
    for attempt in range(max_retries):
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000],
                timeout=30  # 30 second timeout
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                print(f"      ⚠️  Retry {attempt+1}/{max_retries} dans {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"      ❌ Erreur embedding après {max_retries} tentatives: {str(e)}")
                return None

def process_file(file_path):
    """Process file and generate embeddings"""
    ext = file_path.suffix.lower()
    
    # Extract
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        text = extract_text_from_word(file_path)
    elif ext in ['.xlsx', '.xls']:
        text = extract_text_from_excel(file_path)
    else:
        return 0, 0.0
    
    if not text or len(text.strip()) < 100:
        return 0, 0.0
    
    # Chunk
    text_chunks = chunk_text(text)
    if not text_chunks:
        return 0, 0.0
    
    print(f"      📄 {len(text_chunks)} chunks")
    
    # Get/Create document
    file_hash = get_file_hash(file_path)
    
    try:
        doc_result = supabase.table("documents").select("id").eq("file_path", str(file_path)).execute()
        
        if doc_result.data:
            document_id = doc_result.data[0]['id']
        else:
            # Categorize
            name_lower = file_path.name.lower()
            if any(x in name_lower for x in ['bail', 'baux', 'lease']):
                category = 'lease'
            elif any(x in name_lower for x in ['assurance', 'police']):
                category = 'insurance'
            elif any(x in name_lower for x in ['maintenance', 'entretien']):
                category = 'maintenance'
            elif any(x in name_lower for x in ['sinistre', 'incident']):
                category = 'incident'
            elif any(x in name_lower for x in ['litige']):
                category = 'dispute'
            elif any(x in name_lower for x in ['facture', 'invoice']):
                category = 'invoice'
            elif any(x in name_lower for x in ['financier', 'compte', 'resultat']):
                category = 'financial'
            else:
                category = 'other'
            
            # Insert document (without file_hash - not in current schema)
            doc_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_type': ext[1:],
                'category': category
            }
            
            doc_insert = supabase.table("documents").insert(doc_data).execute()
            document_id = doc_insert.data[0]['id']
        
        # Process chunks
        total_cost = 0.0
        chunks_inserted = 0
        
        for idx, current_chunk in enumerate(text_chunks):
            embedding = generate_embedding(current_chunk)
            
            if not embedding:
                continue
            
            # Cost estimation
            words = len(current_chunk.split())
            tokens = words * 1.3
            cost = (tokens / 1000) * 0.0001
            total_cost += cost
            
            # Insert
            try:
                supabase.table("document_chunks").insert({
                    'document_id': document_id,
                    'chunk_number': idx,
                    'chunk_text': current_chunk,
                    'chunk_size': len(current_chunk),
                    'embedding': embedding,
                    'metadata': {
                        'file_name': file_path.name,
                        'file_type': ext[1:],
                        'category': category,
                        'file_hash': file_hash
                    }
                }).execute()
                chunks_inserted += 1
            except Exception as e:
                print(f"      ❌ Erreur insert: {str(e)}")
            
            time.sleep(0.05)
        
        return chunks_inserted, total_cost
        
    except Exception as e:
        print(f"      ❌ Erreur: {str(e)}")
        return 0, 0.0

# Scan new files
print("\n[INFO] Scan fichiers nouveaux (delta)...")
new_files = []

for file_path in ROOT_DIR.rglob('*'):
    if file_path.is_file() and should_process(file_path):
        new_files.append(file_path)

print(f"[OK] {len(new_files)} nouveaux fichiers a embedder\n")

if len(new_files) == 0:
    print("[INFO] Aucun nouveau fichier ! Tout est deja embedder.\n")
    exit(0)

# Load progress
if PROGRESS_FILE.exists():
    with open(PROGRESS_FILE, 'r') as f:
        progress = json.load(f)
else:
    progress = {'processed': [], 'total_chunks': 0, 'total_cost': 0.0}

# Make progress global for signal handler
global_progress = progress

print(f"{'='*80}")
print(f"  TRAITEMENT DELTA")
print(f"{'='*80}\n")
print(f"💾 Auto-sauvegarde: toutes les 10 entrées")
print(f"🔄 Retry API: 3 tentatives max avec timeout 30s")
print(f"⚠️  Ctrl+C: sauvegarde automatique avant arrêt\n")

total_chunks = 0
total_cost = 0.0
processed = 0

with tqdm(total=len(new_files), desc="Embeddings") as pbar:
    for file_path in new_files:
        file_hash = get_file_hash(file_path)
        
        if file_hash in progress['processed']:
            pbar.update(1)
            continue
        
        try:
            print(f"\n📄 {file_path.name}")
            chunks, cost = process_file(file_path)
            
            if chunks > 0:
                total_chunks += chunks
                total_cost += cost
                processed += 1
                print(f"      ✅ {chunks} chunks, ${cost:.4f}")
                
                progress['processed'].append(file_hash)
                progress['total_chunks'] += chunks
                progress['total_cost'] += cost
            
            # Save every 10 files (balance between safety and performance)
            if processed % 10 == 0:
                print(f"      💾 Sauvegarde auto ({processed} fichiers)...")
                with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, indent=2, ensure_ascii=False)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption utilisateur - sauvegarde...")
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
            raise
        
        except Exception as e:
            print(f"      ❌ ERREUR: {str(e)}")
            # Continue with next file
        
        pbar.update(1)

# Save final
print("\n💾 Sauvegarde finale...")
with open(PROGRESS_FILE, 'w') as f:
    json.dump(progress, f, indent=2)

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Nouveaux fichiers: {processed}")
print(f"✅ Nouveaux chunks: {total_chunks}")
print(f"✅ Chunks totaux: {30854 + progress['total_chunks']}")
print(f"💰 Coût session: ${total_cost:.2f}")
print(f"💰 Coût total delta: ${progress['total_cost']:.2f}")

print(f"\n🎉 Embeddings delta terminés !")
print(f"\n📊 BASE COMPLÈTE:")
print(f"   • Ancien projet: 30'854 chunks")
print(f"   • Delta nouveau: {progress['total_chunks']:,} chunks")
print(f"   • TOTAL: {30854 + progress['total_chunks']:,} chunks\n")

print(f"🚀 Prochaine étape: python test_semantic_search.py\n")


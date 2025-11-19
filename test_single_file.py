"""
Test embedding on a single small file
"""
from supabase import create_client
from pathlib import Path
import openai
import time

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"
OPENAI_API_KEY = "your_openai_api_key_here"

print("="*80)
print("  TEST SINGLE FILE EMBEDDING")
print("="*80)

# Init
openai.api_key = OPENAI_API_KEY
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Find smallest file
ROOT_DIR = Path(r"C:\OneDriveExport")
all_files = []
for ext in ['*.pdf', '*.docx', '*.xlsx']:
    all_files.extend(ROOT_DIR.rglob(ext))

if not all_files:
    print("❌ No files found!")
    exit(1)

# Sort by size
all_files_sorted = sorted(all_files, key=lambda x: x.stat().st_size)
test_file = all_files_sorted[0]

print(f"\n📄 Test file: {test_file.name}")
print(f"   Size: {test_file.stat().st_size:,} bytes")

# Simple text extraction
print(f"\n⏳ Extracting text...")
try:
    import PyPDF2
    with open(test_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = reader.pages[0].extract_text()[:1000]  # Just first 1000 chars
    
    print(f"✅ Extracted {len(text)} characters")
    print(f"   Preview: {text[:100]}...")
    
except Exception as e:
    print(f"❌ Extraction error: {e}")
    exit(1)

# Generate embedding
print(f"\n⏳ Generating embedding...")
start = time.time()
try:
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
        timeout=30
    )
    embedding = response.data[0].embedding
    duration = time.time() - start
    
    print(f"✅ Embedding generated in {duration:.1f}s")
    print(f"   Dimensions: {len(embedding)}")
    
except Exception as e:
    print(f"❌ Embedding error: {e}")
    exit(1)

# Insert in DB
print(f"\n⏳ Inserting in DB...")
try:
    result = supabase.table("document_chunks").insert({
        "content": text,
        "embedding": embedding,
        "metadata": {"test": True, "file": test_file.name}
    }).execute()
    
    print(f"✅ Inserted in DB!")
    print(f"   ID: {result.data[0]['id']}")
    
except Exception as e:
    print(f"❌ DB error: {e}")
    exit(1)

print(f"\n{'='*80}")
print("✅ TEST PASSED - All systems working!")
print(f"{'='*80}")



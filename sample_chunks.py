"""Check chunk structure"""
from supabase import create_client

s = create_client(
    'https://reqkkltmtaflbkchsmzb.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc'
)

chunks = s.table('document_chunks').select('chunk_text, metadata').limit(10).execute()

print("="*80)
print("SAMPLE CHUNKS")
print("="*80)

for i, ch in enumerate(chunks.data, 1):
    text = ch.get('chunk_text', '')
    meta = ch.get('metadata')
    
    print(f"\nChunk {i}:")
    print(f"Text: {text[:150]}...")
    print(f"Metadata: {meta}")
    print("-"*80)



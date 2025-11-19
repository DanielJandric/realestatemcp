"""Check if old project has documents table with file paths"""
from supabase import create_client
import json

old_supabase = create_client(
    'https://ugbfpxjpgtbxvcmimsap.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnYmZweGpwZ3RieHZjbWltc2FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjkyMjAzOCwiZXhwIjoyMDc4NDk4MDM4fQ.aTAMaBHhOqSb8mQsAOEeT7d4k21kmlLliM7moUNAkLY'
)

try:
    docs = old_supabase.table('documents_full').select('*').limit(3).execute()
    print('✅ Documents_full table exists in old project!')
    print(f'\n📄 Found {len(docs.data)} documents\n')
    
    for doc in docs.data:
        print(json.dumps(doc, indent=2, default=str))
        print()
    
    if docs.data:
        print('\n🔑 Columns:', list(docs.data[0].keys()))
        
        # Check if we have file paths
        has_file_path = any('path' in str(k).lower() or 'file' in str(k).lower() for k in docs.data[0].keys())
        if has_file_path:
            print('\n✅ File path columns found! Chunks CAN be salvaged!')
        else:
            print('\n❌ No file path columns found. Chunks CANNOT be linked.')
        
except Exception as e:
    print(f'❌ Error accessing documents_full table: {str(e)}')
    print('\n💡 The old project has NO usable documents table')
    print('   The migrated chunks cannot be linked to any files!')


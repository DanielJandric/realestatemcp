from supabase import create_client
import re

s = create_client('https://reqkkltmtaflbkchsmzb.supabase.co','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc')

docs = s.table('documents').select('file_name,file_path').filter('category','eq','lease').execute().data

parking_pattern = r'\bpp\b|parking|garage|place.*parc'

matches = [d for d in docs if re.search(parking_pattern, d['file_name'].lower() + ' ' + d['file_path'].lower())]

print(f"Parkings potentiels: {len(matches)}\n")

for i, d in enumerate(matches[:20], 1):
    print(f"{i}. {d['file_name']}")
    # Show path snippet
    path_lower = d['file_path'].lower()
    if 'pp' in path_lower or 'parking' in path_lower or 'garage' in path_lower:
        path_snippet = d['file_path'].split('\\')[-2] if '\\' in d['file_path'] else ''
        if path_snippet:
            print(f"   Dossier: {path_snippet}")
    print()



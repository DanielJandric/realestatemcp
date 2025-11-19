from supabase import create_client
import re

s = create_client('https://reqkkltmtaflbkchsmzb.supabase.co','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc')

docs = s.table('documents').select('file_name').filter('category','eq','lease').execute().data

# Search for different unit types
types_to_find = {
    'PP/Parking': r'\bpp\b|\bparking\b',
    'Garage': r'\bgarage\b',
    'Box': r'\bbox\b',
    'Cave': r'\bcave\b',
    'Dépôt': r'dépôt|depot',
}

print("Recherche de types spéciaux dans les baux:\n")

for type_name, pattern in types_to_find.items():
    found = [d for d in docs if re.search(pattern, d['file_name'].lower())]
    print(f"{type_name}: {len(found)} trouvés")
    for d in found[:10]:
        print(f"  - {d['file_name']}")
    if len(found) > 10:
        print(f"  ... et {len(found)-10} autres")
    print()



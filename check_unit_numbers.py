from supabase import create_client

s = create_client('https://reqkkltmtaflbkchsmzb.supabase.co','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc')

units = s.table('units').select('unit_number').limit(20).execute().data
docs = s.table('documents').select('file_name').filter('category','eq','lease').limit(10).execute().data

print("Sample unit_numbers from DB:")
for u in units[:10]:
    print(f"  - {u['unit_number']}")

print("\nSample lease filenames:")
for d in docs:
    print(f"  - {d['file_name']}")



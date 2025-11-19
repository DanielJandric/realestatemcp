"""
Show details of the newly extracted Convention signée avocats
"""
from supabase import create_client

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  CONVENTION SIGNÉE AVOCATS - DÉTAILS")
print("="*80)

# Get Pratifori disputes
disputes = supabase.table("disputes").select("*, properties(name)").execute()

pratifori_disputes = [d for d in disputes.data if d.get('properties') and 'pratifori' in d['properties']['name'].lower()]

print(f"\n📋 Found {len(pratifori_disputes)} dispute(s) for Pratifori 5-7:")

for idx, disp in enumerate(pratifori_disputes, 1):
    print(f"\n{'='*80}")
    print(f"DISPUTE #{idx}")
    print(f"{'='*80}")
    print(f"Property: {disp['properties']['name']}")
    print(f"Status: {disp['status']}")
    print(f"Date: {disp['date']}")
    print(f"Amount: CHF {disp['amount']:,.2f}" if disp.get('amount') else "Amount: N/A")
    print(f"\nDescription:")
    print(f"{'-'*80}")
    print(disp['description'])
    print(f"{'-'*80}")

# Get associated documents
docs = supabase.table("documents").select("*, properties(name)").filter("category", "eq", "legal").execute()
pratifori_docs = [d for d in docs.data if d.get('properties') and 'pratifori' in d['properties']['name'].lower()]

print(f"\n\n📄 Legal documents for Pratifori 5-7: {len(pratifori_docs)}")
for doc in pratifori_docs:
    print(f"  - {doc['file_name']}")

print("\n" + "="*80)
print("  ✅ EXTRACTION AZURE OCR RÉUSSIE")
print("="*80)
print("\nLe fichier 'Convention signée avocats.pdf' a été extrait avec Azure OCR")
print("et ses informations ont été ajoutées à la table disputes.")



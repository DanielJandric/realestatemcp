"""
Final summary of dispute imports from Excel and PDF sources
"""
from supabase import create_client

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  FINAL SUMMARY: LITIGES & SINISTRES IMPORT")
print("="*80)

# Get all disputes with property info
disputes = supabase.table("disputes").select("*, properties(name, city)").execute()
incidents = supabase.table("incidents").select("*, properties(name, city)").execute()
documents = supabase.table("documents").select("*, properties(name)").filter("category", "eq", "legal").execute()

print(f"\n📊 DATABASE TOTALS:")
print(f"   - Incidents (sinistres): {len(incidents.data)}")
print(f"   - Disputes (litiges): {len(disputes.data)}")
print(f"   - Legal documents: {len(documents.data)}")

# Disputes by property
print(f"\n" + "="*80)
print(f"  DISPUTES BY PROPERTY")
print(f"="*80)

by_property = {}
for disp in disputes.data:
    prop_name = disp['properties']['name'] if disp.get('properties') else 'Unknown'
    if prop_name not in by_property:
        by_property[prop_name] = []
    by_property[prop_name].append(disp)

for prop_name, disps in sorted(by_property.items()):
    print(f"\n{prop_name}: {len(disps)} dispute(s)")
    for disp in disps:
        status = disp['status'] or 'unknown'
        desc_preview = disp['description'][:80] + "..." if disp['description'] and len(disp['description']) > 80 else disp['description']
        amount = f"CHF {disp['amount']:,.2f}" if disp.get('amount') else "N/A"
        print(f"  [{status:12}] {amount:15} - {desc_preview}")

# Incidents by property
print(f"\n" + "="*80)
print(f"  INCIDENTS BY PROPERTY")
print(f"="*80)

by_property = {}
for inc in incidents.data:
    prop_name = inc['properties']['name'] if inc.get('properties') else 'Unknown'
    if prop_name not in by_property:
        by_property[prop_name] = []
    by_property[prop_name].append(inc)

for prop_name, incs in sorted(by_property.items()):
    print(f"\n{prop_name}: {len(incs)} incident(s)")
    for inc in incs:
        status = inc['status'] or 'unknown'
        desc_preview = inc['description'][:80] + "..." if inc['description'] and len(inc['description']) > 80 else inc['description']
        print(f"  [{status:12}] - {desc_preview}")

# Legal documents by property
print(f"\n" + "="*80)
print(f"  LEGAL DOCUMENTS BY PROPERTY")
print(f"="*80)

by_property = {}
for doc in documents.data:
    prop_name = doc['properties']['name'] if doc.get('properties') else 'Unknown'
    if prop_name not in by_property:
        by_property[prop_name] = []
    by_property[prop_name].append(doc)

for prop_name, docs in sorted(by_property.items()):
    print(f"\n{prop_name}: {len(docs)} document(s)")
    for doc in docs:
        print(f"  - {doc['file_name']}")

print(f"\n" + "="*80)
print(f"  ✅ IMPORT COMPLETE")
print(f"="*80)
print(f"\n📝 Sources:")
print(f"   - Excel files (Litiges.xlsx)")
print(f"   - PDF files (confirmations + actual disputes)")
print(f"   - Manual sinistre tracking spreadsheets")
print(f"\n⚠️  Note: 'Convention signée avocats.pdf' could not be read")
print(f"   (requires Azure OCR for scanned documents)")
print(f"\n💡 To extract that file, add Azure credentials to .env:")
print(f"   AZURE_DOC_INTELLIGENCE_ENDPOINT=https://...")
print(f"   AZURE_DOC_INTELLIGENCE_KEY=your-key")



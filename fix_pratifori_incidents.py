"""
Import the 2 missing Pratifori incidents
"""
from supabase import create_client
import pandas as pd
from datetime import datetime
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*70)
print("  FIXING PRATIFORI INCIDENTS")
print("="*70)

# Get Pratifori 5-7 property ID
pratifori = supabase.table("properties").select("id, name").ilike("name", "%pratifori%").execute()
if not pratifori.data:
    print("❌ Pratifori property not found!")
    exit(1)

property_id = pratifori.data[0]['id']
print(f"\n✅ Found property: {pratifori.data[0]['name']} (ID: {property_id})")

# Read sinistre file
sinistre_file = r"Incremental1\Tableau suivi sinistre.xlsx"
df = pd.read_excel(sinistre_file, sheet_name=0)
df = df.dropna(how='all')

def parse_date(date_val):
    if pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val.date().isoformat()
    try:
        dt = pd.to_datetime(str(date_val).strip())
        return dt.date().isoformat()
    except:
        return None

print("\n Processing Pratifori 7 incidents...")
incidents_created = 0

for idx, row in df.iterrows():
    immeuble = row.get('Immeuble')
    if pd.isna(immeuble):
        continue
    
    # Only process "Pratifori 7"
    if 'pratifori 7' not in str(immeuble).lower():
        continue
    
    locataire = str(row.get('Locataire', '')).strip() if pd.notna(row.get('Locataire')) else None
    assurance = str(row.get("Nom de l'assurance", '')).strip() if pd.notna(row.get("Nom de l'assurance")) else None
    date_sinistre = parse_date(row.get('date du sinistre '))
    cause = str(row.get('cause du sinistre ', '')).strip() if pd.notna(row.get('cause du sinistre ')) else None
    statut = str(row.get('Statut ', '')).strip() if pd.notna(row.get('Statut ')) else 'open'
    
    # Map status
    status_map = {'terminé': 'closed', 'en cours': 'in_progress', 'ouvert': 'open'}
    status = status_map.get(statut.lower(), 'open')
    
    # Build description
    description_parts = []
    if cause:
        description_parts.append(f"Cause: {cause}")
    if assurance:
        description_parts.append(f"Assurance: {assurance}")
    if locataire:
        description_parts.append(f"Locataire: {locataire}")
    
    mise_a_jour = row.get('Mise à jour')
    if pd.notna(mise_a_jour) and str(mise_a_jour).strip() != '-':
        description_parts.append(f"Mise à jour: {mise_a_jour}")
    
    commentaires = row.get('Commentaires Investis ')
    if pd.notna(commentaires) and str(commentaires).strip() != '-':
        description_parts.append(f"Commentaires: {commentaires}")
    
    description = "\n\n".join(description_parts) if description_parts else cause
    
    # Create incident
    incident_data = {
        'property_id': property_id,
        'date': date_sinistre or datetime.now().date().isoformat(),
        'description': description,
        'status': status,
        'insurance_ref': assurance,
    }
    
    try:
        supabase.table("incidents").insert(incident_data).execute()
        incidents_created += 1
        print(f"   ✅ [{incidents_created}] Pratifori 5-7 - {locataire or 'N/A'} ({status})")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print(f"\n✅ Created {incidents_created} incidents for Pratifori 5-7")

# Final count
incidents = supabase.table("incidents").select("*", count="exact").execute()
print(f"\n📊 Total incidents in database: {incidents.count}")



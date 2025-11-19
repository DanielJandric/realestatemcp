"""
Import insurance policies - Extract data from PDF files
"""
from pathlib import Path
from supabase import create_client
import re
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  IMPORT POLICES D'ASSURANCE")
print("="*80)

# Get properties
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

print(f"\n📊 Propriétés dans la base:")
for name in property_by_name.keys():
    print(f"   - {name}")

# Main policy files to process
main_policies = [
    {
        'file': Path(r"Incremental1\Propositions d'assurance\Polices d'assurances\Police du 01.02.2024 au 01.02.2029 - Be Capital SA - Sion.pdf"),
        'properties': ['Gare 28', 'St-Hubert'],
        'owner': 'Be Capital SA',
        'location': 'Sion'
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\Polices d'assurances\Police du 01.02.2024 au 01.02.2029 - Be Capital SA - Aigle.pdf"),
        'properties': ["Pre d'Emoz"],
        'owner': 'Be Capital SA',
        'location': 'Aigle'
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\Polices d'assurances\Police du 08.02.2024 au 01.02.2029 - Audacia Management Sàrl - Martigny.pdf"),
        'properties': ['Gare 8-10', 'Place Centrale 3'],
        'owner': 'Audacia Management Sàrl',
        'location': 'Martigny'
    },
    {
        'file': Path(r'Incremental1\St-Hubert 5 - Sion - DD\02. Assurances\Baloise\Police du 01.01.2025 au 31.12.2027.pdf'),
        'properties': ['St-Hubert'],
        'owner': 'Copropriété',
        'location': 'Sion'
    }
]

def parse_date(date_str):
    """Parse date from DD.MM.YYYY format"""
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date().isoformat()
    except:
        return None

def extract_info_from_filename(filename):
    """Extract dates and info from filename"""
    info = {}
    
    # Extract period (dd.mm.yyyy au dd.mm.yyyy)
    period_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*au\s*(\d{2}\.\d{2}\.\d{4})', filename)
    if period_match:
        info['start_date'] = parse_date(period_match.group(1))
        info['end_date'] = parse_date(period_match.group(2))
    
    # Extract owner
    if 'Be Capital' in filename:
        info['owner'] = 'Be Capital SA'
    elif 'Audacia' in filename:
        info['owner'] = 'Audacia Management Sàrl'
    elif 'Baloise' in filename or 'baloise' in filename.lower():
        info['insurer'] = 'Baloise'
    
    return info

# Create insurance records
insurance_records = []

print(f"\n📄 Traitement des polices...\n")

for policy_info in main_policies:
    file_path = policy_info['file']
    
    if not file_path.exists():
        print(f"   ❌ Fichier non trouvé: {file_path.name}")
        continue
    
    print(f"{'='*80}")
    print(f"📄 {file_path.name}")
    print(f"{'='*80}")
    
    # Extract info from filename
    file_info = extract_info_from_filename(file_path.name)
    
    # For each property in this policy
    for prop_name in policy_info['properties']:
        property_id = property_by_name.get(prop_name)
        
        if not property_id:
            print(f"   ⚠️  Propriété non trouvée: {prop_name}")
            continue
        
        print(f"\n   🏢 {prop_name}")
        
        # Create insurance record
        record = {
            'id': str(uuid.uuid4()),
            'property_id': property_id,
            'policy_type': 'property',  # Default, could be refined with OCR
            'insurer_name': file_info.get('insurer', 'À déterminer'),
            'policy_start_date': file_info.get('start_date'),
            'policy_end_date': file_info.get('end_date'),
            'status': 'active',
            'description': f"Police {policy_info['owner']} - {policy_info['location']}",
            'document_path': str(file_path),
            'created_at': datetime.now().isoformat()
        }
        
        # Add estimated premium (would need OCR to extract)
        # For now, use placeholder
        record['annual_premium'] = 0  # To be updated with OCR
        
        # Add coverage details based on filename/path
        if 'incendie' in file_path.name.lower():
            record['policy_type'] = 'fire'
            record['description'] += ' - Assurance incendie'
        elif 'baloise' in str(file_path).lower():
            record['policy_type'] = 'building'
            record['insurer_name'] = 'Baloise'
        
        insurance_records.append(record)
        
        print(f"      Type: {record['policy_type']}")
        print(f"      Assureur: {record['insurer_name']}")
        print(f"      Période: {record['policy_start_date']} → {record['policy_end_date']}")
        print(f"      Statut: {record['status']}")

# Summary before insert
print(f"\n{'='*80}")
print(f"  RÉSUMÉ")
print(f"{'='*80}\n")

print(f"📊 Polices à insérer: {len(insurance_records)}")

by_type = {}
by_insurer = {}

for rec in insurance_records:
    policy_type = rec['policy_type']
    insurer = rec['insurer_name']
    
    by_type[policy_type] = by_type.get(policy_type, 0) + 1
    by_insurer[insurer] = by_insurer.get(insurer, 0) + 1

print(f"\n📋 Par type:")
for t, count in sorted(by_type.items()):
    print(f"   {t:20}: {count}")

print(f"\n🏢 Par assureur:")
for ins, count in sorted(by_insurer.items()):
    print(f"   {ins:30}: {count}")

# Insert into database
print(f"\n{'='*80}")
print(f"  INSERTION")
print(f"{'='*80}\n")

try:
    supabase.table("insurance_policies").insert(insurance_records).execute()
    print(f"✅ {len(insurance_records)} polices d'assurance insérées!")
    
    print(f"\n💡 NOTE:")
    print(f"   Les primes annuelles (annual_premium) sont à 0")
    print(f"   → Utiliser Azure OCR pour extraire:")
    print(f"      - Montant des primes")
    print(f"      - Valeurs assurées")
    print(f"      - Numéros de police")
    print(f"      - Détails de couverture")
    
except Exception as e:
    print(f"❌ Erreur: {str(e)}")

print(f"\n✅ Import terminé!")


"""
Import maintenance contracts from Excel files to Supabase maintenance table
"""
import pandas as pd
from pathlib import Path
from supabase import create_client
from datetime import datetime
import uuid
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  IMPORT CONTRATS DE MAINTENANCE")
print("="*80)

# Property name mapping
PROPERTY_MAPPING = {
    'gare 8-10': 'Gare 8-10',
    'gare 28': 'Gare 28',
    'centrale 3': 'Place Centrale 3',
    'pl. centrale 3': 'Place Centrale 3',
    'grande avenue': 'Grand Avenue',
    'grande-avenue': 'Grand Avenue',
    'pratifori': 'Pratifori 5-7',
    'banque 4': 'Banque 4',
}

# Files to process
files = [
    {
        'path': r"Incremental1\Gare 8-10 - Martigny - DD\09. Contrats de maintenance\Gare 8-10 Martigny_contrats d'entretien_Màj au 03.10.2024.xlsx",
        'property': 'Gare 8-10'
    },
    {
        'path': r"Incremental1\09. Contrats de maintenance\Becapital_contrats d'entretien_Gare 28 Sion_Màj au 05.09.2024.xlsx",
        'property': 'Gare 28'
    },
    {
        'path': r"Incremental1\Centrale 3 - Martigny - DD\09. Contrats de maintenance\Audacia_contrats d'entretien_Pl. Centrale 3 à Martigny_MàJ au 05.09.2024.xlsx",
        'property': 'Place Centrale 3'
    },
    {
        'path': r"Incremental1\Grande-Avenue 6 - Chippis - DD\08. Contrats de maintenance\Audacia_Contrats d'entretien_GrandeAvenue6 Chippis_07.10.2025.xlsx",
        'property': 'Grand Avenue'
    },
    {
        'path': r"Pratifori 5-7 - Sion - DD\09. Contrats de maintenance\Pratifori 5-7_contrats d'entretien_Màj au 09.10.2025.xlsx",
        'property': 'Pratifori 5-7'
    },
    {
        'path': r"Banque 4 - Fribourg - DD\09. Contrats de maintenance\Banque 4 Fribourg_contrats d'entretien_Màj au 16.07.2025 (PAS ENVOYE).xlsx",
        'property': 'Banque 4'
    }
]

# Get properties from database
print(f"\n📊 Chargement des propriétés...")
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

print(f"   Propriétés disponibles: {list(property_by_name.keys())}")

def parse_date(date_str):
    """Parse date from various formats"""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Try different formats
    formats = [
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d.%m.%y',
        '%d/%m/%y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except:
            pass
    
    return None

def clean_cost(cost_str):
    """Clean and parse annual cost"""
    if pd.isna(cost_str):
        return None
    
    try:
        # Remove spaces, convert comma to dot
        cost_str = str(cost_str).replace("'", "").replace(" ", "").replace(",", ".")
        return float(cost_str)
    except:
        return None

def determine_status(etat_str, fin_contrat):
    """Determine contract status"""
    if pd.isna(etat_str):
        return 'active'
    
    etat_lower = str(etat_str).lower()
    
    if 'résilié' in etat_lower or 'resilié' in etat_lower:
        return 'terminated'
    elif 'à résilier' in etat_lower or 'a résilier' in etat_lower:
        return 'to_terminate'
    elif 'conservé' in etat_lower or 'conserver' in etat_lower:
        return 'active'
    else:
        return 'active'

# Process each file
all_contracts = []
stats = {
    'files_processed': 0,
    'contracts_found': 0,
    'contracts_imported': 0,
    'errors': 0
}

for file_info in files:
    file_path = Path(file_info['path'])
    property_name = file_info['property']
    
    if not file_path.exists():
        print(f"\n❌ Fichier non trouvé: {file_path}")
        continue
    
    print(f"\n{'='*80}")
    print(f"📄 {file_path.name}")
    print(f"   Propriété: {property_name}")
    print(f"{'='*80}")
    
    property_id = property_by_name.get(property_name)
    if not property_id:
        print(f"   ⚠️  Propriété non trouvée dans la base: {property_name}")
        continue
    
    try:
        # Read Excel with correct header
        df = pd.read_excel(file_path, sheet_name=0, header=6)
        
        # Handle files with different number of columns
        num_cols = len(df.columns)
        
        if num_cols == 10:
            df.columns = [
                'vendor_name', 'description', 'frequency', 'annual_cost', 
                'start_date', 'notice_period', 'end_date', 'status_text',
                'remarks_invest', 'remarks_management'
            ]
        elif num_cols == 11:
            # Some files have an extra column (usually at the end)
            df.columns = [
                'vendor_name', 'description', 'frequency', 'annual_cost', 
                'start_date', 'notice_period', 'end_date', 'status_text',
                'remarks_invest', 'remarks_management', 'extra'
            ]
        else:
            print(f"   ⚠️  Nombre de colonnes inattendu: {num_cols}")
            # Try with first 10 columns
            df = df.iloc[:, :10]
            df.columns = [
                'vendor_name', 'description', 'frequency', 'annual_cost', 
                'start_date', 'notice_period', 'end_date', 'status_text',
                'remarks_invest', 'remarks_management'
            ]
        
        # Filter out empty rows
        df = df[df['vendor_name'].notna() & (df['vendor_name'].astype(str).str.strip() != '')]
        
        # Skip header rows that might have been included
        df = df[~df['vendor_name'].astype(str).str.contains('Nom d.*entreprise', case=False, na=False)]
        df = df[~df['vendor_name'].astype(str).str.contains('Contrats', case=False, na=False)]
        
        print(f"   Contrats trouvés: {len(df)}")
        stats['contracts_found'] += len(df)
        
        # Process each contract
        for idx, row in df.iterrows():
            vendor_name = str(row['vendor_name']).strip() if pd.notna(row['vendor_name']) else None
            
            if not vendor_name or vendor_name == '':
                continue
            
            # Build contract data
            contract = {
                'id': str(uuid.uuid4()),
                'property_id': property_id,
                'unit_id': None,  # Could be enhanced with unit matching
                'vendor_name': vendor_name,
                'description': str(row['description']).strip() if pd.notna(row['description']) else None,
                'contract_type': str(row['description']).strip().lower() if pd.notna(row['description']) else 'maintenance',
                'annual_cost': clean_cost(row['annual_cost']),
                'frequency': str(row['frequency']).strip() if pd.notna(row['frequency']) else None,
                'start_date': parse_date(row['start_date']),
                'end_date': parse_date(row['end_date']),
                'status': determine_status(row['status_text'], row['end_date']),
                'created_at': datetime.now().isoformat()
            }
            
            # Add remarks as notes
            remarks = []
            if pd.notna(row['remarks_invest']):
                remarks.append(f"Investis: {row['remarks_invest']}")
            if pd.notna(row['remarks_management']):
                remarks.append(f"Gérance: {row['remarks_management']}")
            
            if remarks:
                if contract['description']:
                    contract['description'] += " | " + " | ".join(remarks)
                else:
                    contract['description'] = " | ".join(remarks)
            
            all_contracts.append(contract)
        
        stats['files_processed'] += 1
        
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        stats['errors'] += 1

# Insert into database
print(f"\n{'='*80}")
print(f"  INSERTION DANS LA BASE DE DONNÉES")
print(f"{'='*80}")

print(f"\n📊 Total contrats à insérer: {len(all_contracts)}")

# Show sample
if all_contracts:
    print(f"\n📋 Échantillon (premiers 5):")
    for i, contract in enumerate(all_contracts[:5], 1):
        print(f"\n{i}. {contract['vendor_name']}")
        print(f"   Type: {contract['contract_type']}")
        print(f"   Coût annuel: {contract['annual_cost']} CHF" if contract['annual_cost'] else "   Coût: N/A")
        print(f"   Début: {contract['start_date']}" if contract['start_date'] else "   Début: N/A")
        print(f"   Statut: {contract['status']}")

# Insert in batches
print(f"\n🔄 Insertion des contrats...")

batch_size = 50
for i in range(0, len(all_contracts), batch_size):
    batch = all_contracts[i:i+batch_size]
    
    try:
        supabase.table("maintenance").insert(batch).execute()
        stats['contracts_imported'] += len(batch)
        print(f"   ✅ {stats['contracts_imported']}/{len(all_contracts)} contrats insérés...")
    except Exception as e:
        print(f"   ❌ Erreur batch {i//batch_size + 1}: {str(e)[:100]}")
        stats['errors'] += 1

# Final statistics
print(f"\n{'='*80}")
print(f"  STATISTIQUES FINALES")
print(f"{'='*80}")

print(f"\n📊 Résumé:")
print(f"   Fichiers traités: {stats['files_processed']}/{len(files)}")
print(f"   Contrats trouvés: {stats['contracts_found']}")
print(f"   Contrats importés: {stats['contracts_imported']}")
print(f"   Erreurs: {stats['errors']}")

# Show distribution by type
if all_contracts:
    from collections import Counter
    types = Counter([c['contract_type'] for c in all_contracts])
    statuses = Counter([c['status'] for c in all_contracts])
    
    print(f"\n📊 Par type de contrat:")
    for t, count in types.most_common(10):
        print(f"   {t:30}: {count:3}")
    
    print(f"\n📊 Par statut:")
    for s, count in statuses.most_common():
        status_labels = {
            'active': 'Actif',
            'terminated': 'Résilié',
            'to_terminate': 'À résilier'
        }
        label = status_labels.get(s, s)
        print(f"   {label:20}: {count:3}")
    
    # Total annual costs
    total_cost = sum(c['annual_cost'] for c in all_contracts if c['annual_cost'])
    active_cost = sum(c['annual_cost'] for c in all_contracts if c['annual_cost'] and c['status'] == 'active')
    
    print(f"\n💰 Coûts annuels:")
    print(f"   Total tous contrats: {total_cost:,.2f} CHF/an")
    print(f"   Total actifs: {active_cost:,.2f} CHF/an")

print(f"\n✅ Import terminé!")


"""
Import financial statements (Compte de Résultat) data
Extract ALL financial data by property
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
print("  IMPORT COMPTE DE RÉSULTAT")
print("="*80)

file_path = Path(r"Incremental1\00. Reporting\2024\Copie de Comptedersultat-436-BeCapitalSABaar20241211-1573736-wpg4qn.xlsx")

# Get properties
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

# Mapping property names
PROPERTY_MAPPING = {
    "pré d'emoz 41-45": "Pre d'Emoz",
    "gare 28": "Gare 28",
    "gare 8-10": "Gare 8-10",
    "banque 4": "Banque 4"
}

print(f"\n📊 Properties dans la base:")
for name in property_by_name.keys():
    print(f"   - {name}")

# Read Excel
print(f"\n📄 Lecture: {file_path.name}\n")

df = pd.read_excel(file_path, sheet_name=0, header=6)

# First row has property names
property_cols = {}
for i, col in enumerate(df.columns):
    val = df.iloc[0, i]
    if pd.notna(val) and val not in ['Compte', 'Désignation', 'Total (Année courante)', '436 (Année courante)']:
        property_cols[col] = str(val).strip()

print(f"🏢 Propriétés trouvées dans le fichier:")
for col, name in property_cols.items():
    mapped = PROPERTY_MAPPING.get(name.lower(), name)
    print(f"   {name} → {mapped}")

# Extract period
period_str = None
for idx in range(5):
    for col in df.columns:
        val = df.iloc[idx, df.columns.get_loc(col)] if col in df.columns else None
        if pd.notna(val) and 'période de décompte' in str(val).lower():
            # Next column should have the period
            next_col_idx = df.columns.get_loc(col) + 1
            if next_col_idx < len(df.columns):
                period_str = df.iloc[idx, next_col_idx]
                break

if period_str:
    print(f"\n📅 Période: {period_str}")
    # Parse dates (format: 01.01.2023 - 10.12.2024)
    match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})', str(period_str))
    if match:
        start_date = datetime.strptime(match.group(1), '%d.%m.%Y').date().isoformat()
        end_date = datetime.strptime(match.group(2), '%d.%m.%Y').date().isoformat()
    else:
        # Default to 2023-2024
        start_date = '2023-01-01'
        end_date = '2024-12-10'
else:
    start_date = '2023-01-01'
    end_date = '2024-12-10'

print(f"   Start: {start_date}")
print(f"   End: {end_date}")

# Skip header row and read data
df_data = df.iloc[1:].copy()

# Rename columns for easier access
new_cols = ['account_code', 'description']
for col in df.columns[2:]:
    new_cols.append(col)
df_data.columns = new_cols[:len(df_data.columns)]

# Filter out empty rows
df_data = df_data[df_data['description'].notna()]

print(f"\n📊 Lignes de données: {len(df_data)}")

# Build financial records per property
financial_records = []

for prop_col, prop_name in property_cols.items():
    mapped_name = PROPERTY_MAPPING.get(prop_name.lower(), prop_name)
    property_id = property_by_name.get(mapped_name)
    
    if not property_id:
        print(f"   ⚠️  Propriété non trouvée: {mapped_name}")
        continue
    
    print(f"\n🏢 Traitement: {mapped_name}")
    
    # Initialize record
    record = {
        'id': str(uuid.uuid4()),
        'property_id': property_id,
        'period_start': start_date,
        'period_end': end_date,
        'rental_income_apartments': 0,
        'rental_income_offices': 0,
        'rental_income_commercial': 0,
        'rental_income_parking': 0,
        'rental_income_other': 0,
        'rental_income_total': 0,
        'vacancy_amount': 0,
        'total_expenses': 0,
        'net_operating_income': 0,
        'created_at': datetime.now().isoformat()
    }
    
    # Extract values
    for idx, row in df_data.iterrows():
        account = str(row['account_code']).strip() if pd.notna(row['account_code']) else ''
        desc = str(row['description']).lower() if pd.notna(row['description']) else ''
        
        # Get value for this property
        value = row.get(prop_col, 0)
        if pd.isna(value):
            value = 0
        try:
            value = float(value)
        except:
            value = 0
        
        # Categorize by account code
        if account.startswith('3000') and 'appartement' in desc:
            record['rental_income_apartments'] += value
        elif account.startswith('3000') and 'bureau' in desc:
            record['rental_income_offices'] += value
        elif account.startswith('3000') and ('métier' in desc or 'commercial' in desc):
            record['rental_income_commercial'] += value
        elif account.startswith('3000') and 'parking' in desc:
            record['rental_income_parking'] += value
        elif account.startswith('3000'):
            record['rental_income_other'] += value
        elif account.startswith('3') and 'recettes' in desc:
            record['rental_income_total'] = value
        elif 'vacant' in desc:
            record['vacancy_amount'] += value
    
    # Calculate total if not already set
    if record['rental_income_total'] == 0:
        record['rental_income_total'] = (
            record['rental_income_apartments'] +
            record['rental_income_offices'] +
            record['rental_income_commercial'] +
            record['rental_income_parking'] +
            record['rental_income_other']
        )
    
    financial_records.append(record)
    
    print(f"   Revenus totaux: {record['rental_income_total']:,.2f} CHF")
    print(f"   - Appartements: {record['rental_income_apartments']:,.2f} CHF")
    print(f"   - Bureaux: {record['rental_income_offices']:,.2f} CHF")
    print(f"   - Commerces: {record['rental_income_commercial']:,.2f} CHF")
    print(f"   - Parkings: {record['rental_income_parking']:,.2f} CHF")
    print(f"   Vacance: {record['vacancy_amount']:,.2f} CHF")

# Insert into database
print(f"\n{'='*80}")
print(f"  INSERTION DANS LA BASE")
print(f"{'='*80}\n")

print(f"📊 Records à insérer: {len(financial_records)}")

try:
    supabase.table("financial_statements").insert(financial_records).execute()
    print(f"\n✅ {len(financial_records)} enregistrements insérés avec succès!")
    
    # Summary
    total_revenue = sum(r['rental_income_total'] for r in financial_records)
    total_vacancy = sum(r['vacancy_amount'] for r in financial_records)
    
    print(f"\n📊 RÉSUMÉ PORTEFEUILLE:")
    print(f"   Revenus locatifs totaux: {total_revenue:,.2f} CHF")
    print(f"   Vacance totale: {total_vacancy:,.2f} CHF")
    print(f"   Taux de vacance: {abs(total_vacancy)/total_revenue*100:.2f}%")
    
except Exception as e:
    print(f"\n❌ Erreur lors de l'insertion: {str(e)}")

print(f"\n✅ Import terminé!")



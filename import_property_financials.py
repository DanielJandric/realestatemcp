"""
Import property financial data from the Excel table
"""
from supabase import create_client
from datetime import datetime
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  IMPORT DONNÉES FINANCIÈRES PROPRIÉTÉS")
print("="*80)

# Data from the image
property_data = [
    {
        'name': "Pre d'Emoz",
        'purchase_price': 10_490_000,
        'valuations': {
            'CBRE': 14_850_000,
            'Cronos': 13_000_000,
            'Beausire': 13_915_733,
            'EDR': 14_600_000,
            'Patrimonium': 15_500_000
        },
        'mortgage': 7_565_000,
        'annual_rent': 621_708,
        'construction': '1990/2006',
        'renovation_type': 'Plat',
        'heating': 'Gaz'
    },
    {
        'name': 'Grand Avenue',
        'purchase_price': 1_900_000,
        'valuations': {
            'CBRE': 2_440_000,
            'Cronos': 2_200_000,
            'Beausire': 2_145_500
        },
        'mortgage': 1_310_000,
        'annual_rent': 129_690,
        'construction': '1925/1987/2010',
        'renovation_type': 'En mansarde',
        'heating': 'Gaz'
    },
    {
        'name': 'Banque 4',
        'purchase_price': 5_593_775,
        'valuations': {
            'CBRE': 7_928_000,
            'Cronos': 7_000_000,
            'Beausire': 7_352_920,
            'EDR': 7_100_000
        },
        'mortgage': 3_400_000,
        'annual_rent': 330_981,
        'construction': '1969/1990',
        'renovation_type': 'Plat',
        'heating': 'Gaz'
    },
    {
        'name': 'Gare 8-10',
        'purchase_price': 13_200_000,
        'valuations': {
            'CBRE': 19_186_000,
            'Cronos': 16_000_000,
            'Beausire': 15_193_051,
            'EDR': 16_800_000
        },
        'mortgage': 9_900_000,
        'annual_rent': 797_635.2,
        'construction': '1961/1992',
        'renovation_type': 'À deux Pans',
        'heating': 'CAD'
    },
    {
        'name': 'Place Centrale 3',
        'purchase_price': 4_280_000,
        'valuations': {
            'CBRE': 4_803_000,
            'Cronos': 4_800_000,
            'Beausire': 5_981_373
        },
        'mortgage': 3_130_000,
        'annual_rent': 283_448,
        'construction': '1919',
        'renovation_type': 'À 2 Pans',
        'heating': 'CAD'
    },
    {
        'name': 'Gare 28',
        'purchase_price': 4_600_000,
        'valuations': {
            'CBRE': 8_742_000,
            'Cronos': 8_250_000,
            'Beausire': 7_906_053,
            'EDR': 9_000_000
        },
        'mortgage': 3_450_000,
        'annual_rent': 422_007,
        'construction': '1970/2024',
        'renovation_type': 'À deux Pans',
        'heating': 'Gaz'
    },
    {
        'name': 'Pratifori 5-7',
        'purchase_price': 16_250_000,
        'valuations': {
            'CBRE': 17_660_000,
            'Cronos': 17_500_000,
            'Beausire': 16_311_840,
            'EDR': 18_500_000,
            'Patrimonium': 15_500_000
        },
        'mortgage': 12_200_000,
        'annual_rent': 815_592,
        'construction': '1991',
        'renovation_type': 'À deux Pans',
        'heating': 'Gaz'
    },
    {
        'name': 'Scex 2-4',
        'purchase_price': 5_100_000,
        'valuations': {
            'CBRE': 19_986_000,
            'Cronos': 16_000_000,
            'Beausire': 16_909_091,
            'EDR': 19_000_000
        },
        'mortgage': 2_900_000,
        'annual_rent': 996_001,
        'construction': '1973',
        'renovation_type': 'Plat',
        'heating': 'Gaz'
    },
    {
        'name': 'St-Hubert',
        'purchase_price': 8_500_000,
        'valuations': {
            'CBRE': 8_826_000,
            'Cronos': 8_800_000,
            'Beausire': 9_465_371
        },
        'mortgage': 6_375_000,
        'annual_rent': 606_936,
        'construction': '1990',
        'renovation_type': 'Plat',
        'heating': 'Gaz'
    }
]

# Get properties from DB
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {}

# Normalize names for matching
for p in properties:
    # Remove accents and normalize
    normalized = p['name'].replace("'", " ").replace("-", " ").lower().strip()
    property_by_name[normalized] = p

print(f"\n📊 Propriétés dans la base: {len(properties)}")
for name in sorted([p['name'] for p in properties]):
    print(f"   - {name}")

def normalize_name(name):
    """Normalize property name for matching"""
    return name.replace("'", " ").replace("-", " ").lower().strip()

def parse_construction_year(construction_str):
    """Parse construction/renovation years"""
    years = re.findall(r'\d{4}', construction_str)
    if not years:
        return None, None
    
    construction_year = int(years[0])
    renovation_year = int(years[-1]) if len(years) > 1 else None
    
    return construction_year, renovation_year

print(f"\n📄 Traitement de {len(property_data)} propriétés...\n")

property_updates = []
valuations_to_insert = []

matched = 0
not_matched = []

for data in property_data:
    normalized = normalize_name(data['name'])
    
    # Try exact match first
    property_db = property_by_name.get(normalized)
    
    # Try partial match
    if not property_db:
        for db_name, db_prop in property_by_name.items():
            if normalized in db_name or db_name in normalized:
                property_db = db_prop
                break
    
    if not property_db:
        not_matched.append(data['name'])
        print(f"❌ Non trouvé: {data['name']}")
        continue
    
    matched += 1
    prop_id = property_db['id']
    prop_name = property_db['name']
    
    print(f"{'='*80}")
    print(f"🏢 {prop_name}")
    print(f"{'='*80}")
    
    # Parse construction years
    construction_year, renovation_year = parse_construction_year(data['construction'])
    
    # Prepare property update
    update_data = {
        'purchase_price': data['purchase_price'],
        'mortgage_amount': data['mortgage'],
        'annual_rental_income': data['annual_rent'],
        'construction_year': construction_year,
        'renovation_year': renovation_year,
        'renovation_type': data['renovation_type'],
        'heating_type': data['heating']
    }
    
    print(f"\n   💰 Données financières:")
    print(f"      Prix d'achat        : {data['purchase_price']:>15,.0f} CHF")
    print(f"      Hypothèque          : {data['mortgage']:>15,.0f} CHF")
    print(f"      Loyers annuels      : {data['annual_rent']:>15,.2f} CHF")
    print(f"      Equity              : {data['purchase_price'] - data['mortgage']:>15,.0f} CHF")
    
    print(f"\n   🏗️  Données techniques:")
    print(f"      Construction        : {construction_year}")
    if renovation_year:
        print(f"      Rénovation          : {renovation_year}")
    print(f"      Type toiture        : {data['renovation_type']}")
    print(f"      Chauffage           : {data['heating']}")
    
    # Valuations
    print(f"\n   📊 Valorisations:")
    for source, amount in data['valuations'].items():
        print(f"      {source:15} : {amount:>15,.0f} CHF")
        
        valuations_to_insert.append({
            'property_id': prop_id,
            'valuation_date': '2024-01-25',  # Approximate date
            'valuation_source': source,
            'valuation_amount': amount,
            'valuation_type': 'market_value',
            'appraiser_name': source
        })
    
    # Calculate appreciation
    avg_valuation = sum(data['valuations'].values()) / len(data['valuations'])
    appreciation = ((avg_valuation - data['purchase_price']) / data['purchase_price'] * 100)
    gain = avg_valuation - data['purchase_price']
    
    print(f"\n   📈 Performance:")
    print(f"      Valorisation moyenne: {avg_valuation:>15,.0f} CHF")
    print(f"      Plus-value          : {gain:>15,.0f} CHF ({appreciation:>5.1f}%)")
    print(f"      Rendement brut      : {data['annual_rent'] / data['purchase_price'] * 100:>5.2f}%")
    
    property_updates.append((prop_id, update_data))
    print()

# Apply updates
print(f"{'='*80}")
print(f"  MISE À JOUR BASE DE DONNÉES")
print(f"{'='*80}\n")

print(f"📊 Résumé:")
print(f"   Propriétés matchées     : {matched}/{len(property_data)}")
if not_matched:
    print(f"   Non matchées            : {', '.join(not_matched)}")

# Update properties
print(f"\n🔄 Mise à jour propriétés...")
updated_count = 0
for prop_id, update_data in property_updates:
    try:
        supabase.table("properties").update(update_data).eq("id", prop_id).execute()
        updated_count += 1
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")

print(f"   ✅ {updated_count} propriétés mises à jour")

# Insert valuations
print(f"\n💎 Insertion valorisations...")
try:
    supabase.table("property_valuations").insert(valuations_to_insert).execute()
    print(f"   ✅ {len(valuations_to_insert)} valorisations insérées")
except Exception as e:
    print(f"   ❌ Erreur: {str(e)}")

# Final statistics
print(f"\n{'='*80}")
print(f"  STATISTIQUES FINALES")
print(f"{'='*80}\n")

total_purchase = sum(d['purchase_price'] for d in property_data)
total_mortgage = sum(d['mortgage'] for d in property_data)
total_equity = total_purchase - total_mortgage
total_rent = sum(d['annual_rent'] for d in property_data)

# Average valuation
all_valuations = []
for d in property_data:
    all_valuations.extend(d['valuations'].values())
avg_total_valuation = sum(all_valuations) / len(property_data)

total_current_value = avg_total_valuation * len(property_data)
total_appreciation = total_current_value - total_purchase

print(f"💰 PORTEFEUILLE GLOBAL:")
print(f"   Prix d'achat total      : {total_purchase:>20,.0f} CHF")
print(f"   Hypothèques totales     : {total_mortgage:>20,.0f} CHF")
print(f"   Equity (fonds propres)  : {total_equity:>20,.0f} CHF ({total_equity/total_purchase*100:.1f}%)")
print(f"   Loyers annuels totaux   : {total_rent:>20,.2f} CHF")
print(f"   Rendement brut moyen    : {total_rent/total_purchase*100:>20.2f}%")
print(f"\n   Valorisation estimée    : {total_current_value:>20,.0f} CHF")
print(f"   Plus-value latente      : {total_appreciation:>20,.0f} CHF ({total_appreciation/total_purchase*100:.1f}%)")

print(f"\n✅ Import terminé!\n")


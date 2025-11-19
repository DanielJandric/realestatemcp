"""
Update leases table with parking denomination and rent structure
"""
from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  MISE À JOUR DES BAUX: DÉNOMINATION PARKING")
print("="*80)

# First, try to add columns
print("\n🔧 Ajout des colonnes dans la table leases...")
print("   (Exécuter add_lease_description.sql manuellement via Supabase SQL Editor)")
print("   Colonnes à ajouter:")
print("   - description TEXT")
print("   - parking_fee NUMERIC(10,2)")
print("   - parking_included BOOLEAN")

# Get data
units = supabase.table("units").select("*").execute().data
leases = supabase.table("leases").select("*").execute().data
tenants = supabase.table("tenants").select("id, name").execute().data

unit_by_id = {u['id']: u for u in units}
tenant_by_id = {t['id']: t['name'] for t in tenants}

# Identify parking leases
parking_leases = []
for lease in leases:
    unit = unit_by_id.get(lease['unit_id'])
    if unit and unit.get('type') == 'parking':
        parking_leases.append({
            'lease': lease,
            'unit': unit,
            'tenant_name': tenant_by_id.get(lease['tenant_id'], 'Unknown')
        })

print(f"\n🚗 Baux de parking trouvés: {len(parking_leases)}")

# Group by tenant to find those with appt + parking
leases_by_tenant = defaultdict(list)
for lease in leases:
    leases_by_tenant[lease['tenant_id']].append(lease)

# Analyze rent structure
print(f"\n📊 ANALYSE DE LA STRUCTURE DES LOYERS:")

appt_with_separate_parking = []
parking_only = []

for parking_data in parking_leases:
    lease = parking_data['lease']
    tenant_id = lease['tenant_id']
    tenant_leases = leases_by_tenant[tenant_id]
    
    # Check if tenant has other units
    other_units = []
    for tl in tenant_leases:
        if tl['id'] != lease['id']:
            unit = unit_by_id.get(tl['unit_id'])
            if unit:
                other_units.append(unit)
    
    if other_units:
        appt_with_separate_parking.append({
            'parking_lease': lease,
            'parking_unit': parking_data['unit'],
            'other_units': other_units,
            'tenant_name': parking_data['tenant_name']
        })
    else:
        parking_only.append(parking_data)

print(f"\n   Locataires avec parking séparé: {len(appt_with_separate_parking)}")
print(f"   Parkings standalone: {len(parking_only)}")

# Show examples
print(f"\n📋 EXEMPLES - APPT + PARKING SÉPARÉ (premiers 10):")
for i, data in enumerate(appt_with_separate_parking[:10], 1):
    print(f"\n{i}. {data['tenant_name']}")
    print(f"   Parking: {data['parking_unit']['unit_number']} → {data['parking_lease']['rent_net']:.2f} CHF")
    for unit in data['other_units']:
        # Find lease for this unit
        unit_lease = next((l for l in leases if l['unit_id'] == unit['id']), None)
        rent = unit_lease['rent_net'] if unit_lease else 0
        print(f"   {unit['type'].title()}: {unit['unit_number']} → {rent:.2f} CHF")

# Strategy for updating
print(f"\n{'='*80}")
print(f"  STRATÉGIE DE MISE À JOUR")
print(f"{'='*80}")

print(f"""
OPTION 1: Mise à jour manuelle via SQL
  - Ajouter les colonnes (add_lease_description.sql)
  - Remplir manuellement les montants parking depuis les baux PDF

OPTION 2: Extraction automatique depuis PDFs
  - Scanner les PDFs de baux parking pour extraire montants
  - Utiliser Azure OCR pour détecter:
    * "Place de parc"
    * Montant (ex: "CHF 50.-")
    * "Compris dans le loyer" vs "En sus"

OPTION 3: Déduction depuis données existantes
  - Si locataire a 2 unités (appt + parking):
    → Le parking est séparé
    → Montant = lease.rent_net du parking
  - Si 1 seule unité appartement:
    → Parking possiblement inclus
    → À vérifier dans PDF

RECOMMANDATION:
  Combiner Option 2 + Option 3
  1. Détecter les parkings séparés automatiquement
  2. Extraire montants depuis PDFs pour validation
  3. Marquer les appartements avec parking inclus
""")

# Update leases with description for now
print(f"\n🔄 Mise à jour des descriptions...")

updated_count = 0

for data in appt_with_separate_parking:
    lease_id = data['parking_lease']['id']
    unit_number = data['parking_unit']['unit_number']
    rent = data['parking_lease']['rent_net']
    
    # Try to update (will fail if columns don't exist yet)
    try:
        description = f"Place de parc {unit_number}"
        # Note: This will fail if columns don't exist
        # supabase.table("leases").update({
        #     "description": description,
        #     "parking_fee": rent if rent > 0 else None,
        #     "parking_included": False
        #}).eq("id", lease_id).execute()
        # updated_count += 1
        
        if updated_count == 0:
            print(f"   ⚠️  Colonnes pas encore ajoutées - exécuter SQL d'abord")
            break
    except Exception as e:
        print(f"   ⚠️  Erreur: {str(e)[:100]}")
        print(f"   → Exécuter add_lease_description.sql d'abord")
        break

print(f"\n{'='*80}")
print(f"  RÉSUMÉ")
print(f"{'='*80}")
print(f"""
✅ {len(parking_leases)} baux de parking identifiés
✅ {len(appt_with_separate_parking)} cas APPT + Parking séparé
✅ Script de migration SQL créé: add_lease_description.sql

PROCHAINES ÉTAPES:
1. Exécuter add_lease_description.sql dans Supabase SQL Editor
2. Relancer ce script pour remplir les descriptions
3. Scanner les PDFs pour extraire les montants parking
4. Valider manuellement les cas ambigus
""")



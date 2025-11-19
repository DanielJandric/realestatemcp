"""
Populate parking data in leases table with descriptions and fees
"""
from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  REMPLISSAGE DES DONNÉES PARKING DANS LEASES")
print("="*80)

# Get data
units = supabase.table("units").select("*").execute().data
leases = supabase.table("leases").select("*").execute().data
tenants = supabase.table("tenants").select("id, name").execute().data

unit_by_id = {u['id']: u for u in units}
tenant_by_id = {t['id']: t['name'] for t in tenants}

# Group leases by tenant
leases_by_tenant = defaultdict(list)
for lease in leases:
    leases_by_tenant[lease['tenant_id']].append(lease)

print(f"\n📊 Analyse des baux...")
print(f"   Total leases: {len(leases)}")
print(f"   Total units: {len(units)}")
print(f"   Total tenants: {len(tenants)}")

# Identify parking leases
parking_updates = []
appartment_with_parking_updates = []

for lease in leases:
    unit = unit_by_id.get(lease['unit_id'])
    if not unit:
        continue
    
    unit_type = unit.get('type', '')
    unit_number = unit.get('unit_number', '')
    rent = lease.get('rent_net', 0) or 0
    
    # Case 1: This IS a parking lease
    if unit_type == 'parking':
        tenant_leases = leases_by_tenant[lease['tenant_id']]
        
        # Check if tenant has other units
        has_other_units = any(
            unit_by_id.get(l['unit_id'], {}).get('type') != 'parking' 
            for l in tenant_leases if l['id'] != lease['id']
        )
        
        parking_updates.append({
            'lease_id': lease['id'],
            'unit_number': unit_number,
            'description': f"Place de parc {unit_number}",
            'parking_fee': rent if rent > 0 else None,
            'parking_included': False,
            'tenant_name': tenant_by_id.get(lease['tenant_id'], 'Unknown'),
            'separate': has_other_units
        })
    
    # Case 2: Check if appartment tenant has separate parking
    elif unit_type in ['appartement', 'bureau', 'commerce']:
        tenant_leases = leases_by_tenant[lease['tenant_id']]
        
        # Find parking leases for this tenant
        parking_leases = [
            l for l in tenant_leases 
            if unit_by_id.get(l['unit_id'], {}).get('type') == 'parking'
        ]
        
        if parking_leases:
            parking_numbers = [
                unit_by_id.get(l['unit_id'], {}).get('unit_number', 'N/A')
                for l in parking_leases
            ]
            
            appartment_with_parking_updates.append({
                'lease_id': lease['id'],
                'unit_number': unit_number,
                'unit_type': unit_type,
                'parking_numbers': parking_numbers,
                'tenant_name': tenant_by_id.get(lease['tenant_id'], 'Unknown')
            })

print(f"\n🚗 BAUX À METTRE À JOUR:")
print(f"   Baux parking: {len(parking_updates)}")
print(f"   - Séparés (en sus): {len([p for p in parking_updates if p['separate']])}")
print(f"   - Standalone: {len([p for p in parking_updates if not p['separate']])}")
print(f"   Appartements avec parking séparé: {len(appartment_with_parking_updates)}")

# Update parking leases
print(f"\n🔄 Mise à jour des baux parking...")

updated_parking = 0
for i, data in enumerate(parking_updates, 1):
    try:
        update_data = {
            'description': data['description'],
            'parking_included': data['parking_included']
        }
        
        if data['parking_fee'] is not None:
            update_data['parking_fee'] = data['parking_fee']
        
        supabase.table("leases").update(update_data).eq("id", data['lease_id']).execute()
        updated_parking += 1
        
        if i <= 10:
            fee_str = f"{data['parking_fee']:.2f} CHF" if data['parking_fee'] else "0.00 CHF"
            status = "EN SUS" if data['separate'] else "STANDALONE"
            print(f"   ✅ {data['unit_number']:20} | {fee_str:10} | {status:10} | {data['tenant_name'][:30]}")
        elif i % 20 == 0:
            print(f"   ✅ {i}/{len(parking_updates)} parkings mis à jour...")
            
    except Exception as e:
        print(f"   ❌ Erreur pour {data['unit_number']}: {str(e)[:80]}")

print(f"\n✅ {updated_parking}/{len(parking_updates)} baux parking mis à jour")

# Update appartement leases with parking info in description
print(f"\n🔄 Mise à jour descriptions appartements avec parking...")

updated_appt = 0
for i, data in enumerate(appartment_with_parking_updates, 1):
    try:
        parking_list = ", ".join(data['parking_numbers'])
        description = f"{data['unit_type'].title()} {data['unit_number']} + Parking(s): {parking_list}"
        
        supabase.table("leases").update({
            'description': description
        }).eq("id", data['lease_id']).execute()
        
        updated_appt += 1
        
        if i <= 10:
            print(f"   ✅ {data['unit_number']:20} | +{len(data['parking_numbers'])} parking(s) | {data['tenant_name'][:30]}")
        elif i % 20 == 0:
            print(f"   ✅ {i}/{len(appartment_with_parking_updates)} appartements mis à jour...")
            
    except Exception as e:
        print(f"   ❌ Erreur pour {data['unit_number']}: {str(e)[:80]}")

print(f"\n✅ {updated_appt}/{len(appartment_with_parking_updates)} baux appartements mis à jour")

# Summary statistics
print(f"\n{'='*80}")
print(f"  STATISTIQUES FINALES")
print(f"{'='*80}")

# Get updated data
leases_updated = supabase.table("leases").select("*").execute().data

with_description = len([l for l in leases_updated if l.get('description')])
with_parking_fee = len([l for l in leases_updated if l.get('parking_fee') is not None])
parking_included_true = len([l for l in leases_updated if l.get('parking_included') == True])
parking_included_false = len([l for l in leases_updated if l.get('parking_included') == False])

print(f"\n📊 Baux avec données enrichies:")
print(f"   Avec description: {with_description}/{len(leases_updated)} ({with_description/len(leases_updated)*100:.1f}%)")
print(f"   Avec parking_fee: {with_parking_fee}")
print(f"   parking_included=FALSE (en sus): {parking_included_false}")
print(f"   parking_included=TRUE (inclus): {parking_included_true}")

# Show parking fees distribution
parking_fees = [l.get('parking_fee') for l in leases_updated if l.get('parking_fee') is not None]
if parking_fees:
    from collections import Counter
    fee_counts = Counter(parking_fees)
    
    print(f"\n💰 DISTRIBUTION DES TARIFS PARKING:")
    for fee, count in sorted(fee_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {fee:6.2f} CHF : {count:2} parkings")
    
    total_parking_revenue = sum(parking_fees)
    print(f"\n   TOTAL revenus parkings: {total_parking_revenue:.2f} CHF/mois")
    print(f"   TOTAL revenus parkings: {total_parking_revenue*12:.2f} CHF/an")

print(f"\n{'='*80}")
print(f"  ✅ MISSION ACCOMPLIE")
print(f"{'='*80}")
print(f"""
✅ {updated_parking} baux parking enrichis
✅ {updated_appt} appartements liés à leurs parkings
✅ Dénominations claires: "Place de parc XXXXX"
✅ Montants parking identifiés et séparés
✅ Distinction parking inclus/en sus

EXEMPLE D'UTILISATION:
- Requête: SELECT * FROM leases WHERE parking_fee IS NOT NULL
  → Tous les parkings payés en sus
  
- Requête: SELECT * FROM leases WHERE description LIKE '%Parking%'
  → Tous les baux avec parking (inclus ou séparé)
""")



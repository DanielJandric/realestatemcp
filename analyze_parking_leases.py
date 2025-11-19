"""
Analyze parking leases structure to understand rent breakdown
"""
from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  ANALYSE STRUCTURE PARKINGS & LOYERS")
print("="*80)

# Get schema of leases table
print("\n📋 SCHEMA de la table LEASES:")
leases_sample = supabase.table("leases").select("*").limit(1).execute().data
if leases_sample:
    for key in sorted(leases_sample[0].keys()):
        value = leases_sample[0][key]
        value_type = type(value).__name__
        print(f"   {key:25} : {value_type:15} = {value}")

# Get schema of units table
print(f"\n📋 SCHEMA de la table UNITS:")
units_sample = supabase.table("units").select("*").limit(1).execute().data
if units_sample:
    for key in sorted(units_sample[0].keys()):
        value = units_sample[0][key]
        value_type = type(value).__name__
        print(f"   {key:25} : {value_type:15} = {value}")

# Get all parking units and their leases
print(f"\n{'='*80}")
print(f"  ANALYSE DES PARKINGS")
print(f"{'='*80}")

parking_units = supabase.table("units").select("*").eq("type", "parking").execute().data
print(f"\n🚗 Parkings trouvés: {len(parking_units)}")

leases = supabase.table("leases").select("*").execute().data
units = supabase.table("units").select("*").execute().data
tenants = supabase.table("tenants").select("id, name").execute().data

# Build lookups
lease_by_unit = {l['unit_id']: l for l in leases}
tenant_by_id = {t['id']: t['name'] for t in tenants}

# Analyze parking leases
print(f"\n📊 EXEMPLES DE PARKINGS (premiers 10):")

for i, parking in enumerate(parking_units[:10], 1):
    lease = lease_by_unit.get(parking['id'])
    if lease:
        tenant_name = tenant_by_id.get(lease['tenant_id'], 'Unknown')
        rent = lease.get('rent_amount', 0) or 0
        
        print(f"\n{i}. {parking['unit_number']} - {tenant_name}")
        print(f"   Loyer: {rent:.2f} CHF")
        print(f"   Type: {parking.get('type')}")
        print(f"   Surface: {parking.get('surface_area', 0)} m²")
        print(f"   Floor: {parking.get('floor', 'N/A')}")

# Check if there are units with multiple leases (appartement + parking)
print(f"\n{'='*80}")
print(f"  ANALYSE: LOCATAIRES AVEC PLUSIEURS UNITÉS")
print(f"{'='*80}")

# Group leases by tenant
leases_by_tenant = defaultdict(list)
for lease in leases:
    leases_by_tenant[lease['tenant_id']].append(lease)

# Find tenants with multiple units
multi_unit_tenants = {tid: ls for tid, ls in leases_by_tenant.items() if len(ls) > 1}

print(f"\n👥 Locataires avec plusieurs unités: {len(multi_unit_tenants)}")

unit_by_id = {u['id']: u for u in units}

# Show examples
print(f"\n📋 EXEMPLES (premiers 10):")
for i, (tenant_id, tenant_leases) in enumerate(list(multi_unit_tenants.items())[:10], 1):
    tenant_name = tenant_by_id.get(tenant_id, 'Unknown')
    print(f"\n{i}. {tenant_name} - {len(tenant_leases)} unités:")
    
    total_rent = 0
    has_parking = False
    has_appt = False
    
    for lease in tenant_leases:
        unit = unit_by_id.get(lease['unit_id'])
        if unit:
            unit_type = unit.get('type', 'unknown')
            rent = lease.get('rent_amount', 0) or 0
            total_rent += rent
            
            if unit_type == 'parking':
                has_parking = True
            if unit_type == 'appartement':
                has_appt = True
            
            print(f"   - {unit['unit_number']:20} | {unit_type:12} | {rent:7.2f} CHF")
    
    print(f"   TOTAL: {total_rent:.2f} CHF", end="")
    if has_parking and has_appt:
        print(" ✅ APPT + PARKING")
    else:
        print()

# Summary statistics
print(f"\n{'='*80}")
print(f"  STATISTIQUES RÉSUMÉES")
print(f"{'='*80}")

parking_leases_count = len([l for l in leases if unit_by_id.get(l['unit_id'], {}).get('type') == 'parking'])
parking_with_rent = len([l for l in leases if unit_by_id.get(l['unit_id'], {}).get('type') == 'parking' and (l.get('rent_amount') or 0) > 0])

appt_with_parking = len([tid for tid, ls in multi_unit_tenants.items() 
                         if any(unit_by_id.get(l['unit_id'], {}).get('type') == 'parking' for l in ls)
                         and any(unit_by_id.get(l['unit_id'], {}).get('type') == 'appartement' for l in ls)])

print(f"\n🚗 Parkings avec bail: {parking_leases_count}")
print(f"💰 Parkings avec loyer > 0: {parking_with_rent}")
print(f"🏠 Locataires avec APPT + Parking: {appt_with_parking}")
print(f"👥 Locataires avec unités multiples: {len(multi_unit_tenants)}")

# Check average parking rent
parking_rents = [l.get('rent_amount', 0) or 0 for l in leases 
                 if unit_by_id.get(l['unit_id'], {}).get('type') == 'parking']
if parking_rents:
    avg_parking_rent = sum(parking_rents) / len(parking_rents)
    max_parking_rent = max(parking_rents)
    min_parking_rent = min([r for r in parking_rents if r > 0], default=0)
    
    print(f"\n💵 LOYERS PARKINGS:")
    print(f"   Moyenne: {avg_parking_rent:.2f} CHF")
    print(f"   Min (>0): {min_parking_rent:.2f} CHF")
    print(f"   Max: {max_parking_rent:.2f} CHF")
    print(f"   Parkings gratuits: {len([r for r in parking_rents if r == 0])}")

print(f"\n{'='*80}")
print(f"  CONCLUSION")
print(f"{'='*80}")
print(f"""
Si un locataire a:
  - 1 bail appartement (ex: 500 CHF)
  - 1 bail parking séparé (ex: 50 CHF)
  
→ Le parking est PAYÉ EN SUS, et le montant est indiqué dans lease.rent_amount

Si le locataire a seulement 1 bail appartement:
  → Le parking PEUT être inclus dans le loyer net
  → Vérifier dans le PDF du bail pour confirmation
""")



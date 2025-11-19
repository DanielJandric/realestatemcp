"""
Detect parkings using metadata: floor=exterieur, surface=0, rooms=0
"""
from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  DÉTECTION PARKINGS PAR MÉTADONNÉES")
print("="*80)

# Get all units
units = supabase.table("units").select("*").execute().data

print(f"\n📊 Total units: {len(units)}")

# Analyze metadata patterns
print(f"\n🔍 Analyse des métadonnées...")

# Find units matching parking criteria
parking_candidates = []

for unit in units:
    floor = str(unit.get('floor', '')).lower() if unit.get('floor') else ''
    surface = unit.get('surface_area', 0) or 0
    rooms = unit.get('rooms', 0) or 0
    
    # Parking criteria: floor=exterieur OR (surface=0 AND rooms=0)
    is_parking_candidate = False
    reason = []
    
    if 'exterieur' in floor or 'ext' in floor:
        is_parking_candidate = True
        reason.append("floor=exterieur")
    
    if surface == 0 and rooms == 0:
        is_parking_candidate = True
        reason.append("surface=0 & rooms=0")
    
    if is_parking_candidate:
        parking_candidates.append({
            'unit': unit,
            'reason': ', '.join(reason)
        })

print(f"\n✅ Parkings potentiels trouvés: {len(parking_candidates)}")

# Show sample
print(f"\n📋 Échantillon (premiers 10):")
for i, candidate in enumerate(parking_candidates[:10], 1):
    unit = candidate['unit']
    print(f"{i:2}. {unit['unit_number']:20} | Type actuel: {unit.get('type', 'None'):15} | {candidate['reason']}")

# Update all parking candidates
print(f"\n🔄 Mise à jour des units en 'parking'...")

updated_count = 0
updates_by_type = defaultdict(int)

for candidate in parking_candidates:
    unit = candidate['unit']
    current_type = unit.get('type', 'appartement')
    
    if current_type != 'parking':
        try:
            supabase.table("units").update({"type": "parking"}).eq("id", unit['id']).execute()
            updated_count += 1
            updates_by_type[current_type] += 1
            
            if updated_count % 25 == 0:
                print(f"   ✅ {updated_count} units mis à jour...")
        except Exception as e:
            pass

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}")
print(f"\n✅ Units mis à jour: {updated_count}")

if updates_by_type:
    print(f"\nMises à jour par type original:")
    for t, count in sorted(updates_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t:15} → parking: {count:3}")

# Final distribution
units_final = supabase.table("units").select("type").execute().data
type_counts = defaultdict(int)
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts[t] += 1

print(f"\n📊 DISTRIBUTION FINALE:")
for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    bar = '█' * int(percent / 2.5)
    print(f"   {t:15}: {count:3} ({percent:5.1f}%) {bar}")

specialty_units = len([u for u in units_final if u.get('type') and u['type'] != 'appartement'])
print(f"\n✅ {len(type_counts)} catégories")
print(f"✅ {specialty_units} unités spécialisées ({specialty_units/len(units_final)*100:.1f}%)")
print(f"\n🎯 Parkings correctement détectés via métadonnées!")



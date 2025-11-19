"""
Add insurance records for missing properties (Pratifori 5-7, Banque 4, Grand Avenue)
These might be covered under portfolio-wide policies
"""
from supabase import create_client
from datetime import datetime
import uuid

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  AJOUT ASSURANCES PROPRIÉTÉS MANQUANTES")
print("="*80)

# Get properties
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

# Check which properties already have insurance
existing = supabase.table("insurance_policies").select("property_id").execute().data
existing_property_ids = set(ins['property_id'] for ins in existing)

print(f"\n📊 Propriétés avec assurance:")
for prop in properties:
    if prop['id'] in existing_property_ids:
        print(f"   ✅ {prop['name']}")
    else:
        print(f"   ❌ {prop['name']} - MANQUANT")

# Properties to add
missing_properties = []
for prop in properties:
    if prop['id'] not in existing_property_ids:
        missing_properties.append(prop)

print(f"\n🔧 Ajout de {len(missing_properties)} propriétés manquantes...\n")

new_records = []

for prop in missing_properties:
    # Determine likely insurer based on property
    if 'Pratifori' in prop['name']:
        # Pratifori is in Sion, likely covered by Be Capital SA - Sion
        insurer = "Be Capital SA (via police Sion)"
        policy_type = "property"
        start_date = "2024-02-01"
        end_date = "2029-02-01"
        notes = "Couverture probable via police Be Capital SA - Sion. À confirmer."
    elif 'Banque' in prop['name']:
        # Banque 4 is in Fribourg, might have separate coverage
        insurer = "À déterminer"
        policy_type = "property"
        start_date = "2024-02-01"
        end_date = "2029-02-01"
        notes = "Police d'assurance à identifier. Dossier 02. Assurances vide."
    elif 'Grand' in prop['name'] or 'Avenue' in prop['name']:
        # Grand Avenue in Chippis
        insurer = "À déterminer"
        policy_type = "property"
        start_date = "2024-02-01"
        end_date = "2029-02-01"
        notes = "Police d'assurance à identifier. Dossier 02. Assurances vide."
    else:
        insurer = "À déterminer"
        policy_type = "property"
        start_date = "2024-02-01"
        end_date = "2029-02-01"
        notes = "Police d'assurance à identifier."
    
    record = {
        'id': str(uuid.uuid4()),
        'property_id': prop['id'],
        'policy_type': policy_type,
        'insurer_name': insurer,
        'policy_start_date': start_date,
        'policy_end_date': end_date,
        'annual_premium': 0,  # Unknown
        'status': 'to_verify',  # Special status for unconfirmed policies
        'description': f"Police à vérifier/identifier pour {prop['name']}",
        'notes': notes,
        'created_at': datetime.now().isoformat()
    }
    
    new_records.append(record)
    
    print(f"   🏢 {prop['name']}")
    print(f"      Assureur: {insurer}")
    print(f"      Période: {start_date} → {end_date}")
    print(f"      Statut: to_verify")
    print(f"      Note: {notes}\n")

# Insert
if new_records:
    print(f"{'='*80}")
    print(f"  INSERTION")
    print(f"{'='*80}\n")
    
    try:
        supabase.table("insurance_policies").insert(new_records).execute()
        print(f"✅ {len(new_records)} enregistrements ajoutés!")
        
        # Final count
        total = supabase.table("insurance_policies").select("*", count="exact").execute().count
        print(f"\n📊 Total polices dans la base: {total}")
        
        # By property
        all_policies = supabase.table("insurance_policies").select("property_id").execute().data
        properties_with_insurance = len(set(p['property_id'] for p in all_policies))
        
        print(f"🏢 Propriétés couvertes: {properties_with_insurance}/{len(properties)}")
        
        if properties_with_insurance == len(properties):
            print(f"\n✅ TOUTES les propriétés ont maintenant une assurance!")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
else:
    print("\n✅ Toutes les propriétés ont déjà une assurance!")

print(f"\n✅ Terminé!")



#!/usr/bin/env python3
"""
Fix unit types intelligently based on unit_number, metadata and tenant info
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import re

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Get all units with property and lease info
result = supabase.rpc('exec_sql', {'sql': """
    SELECT 
        u.id as unit_id,
        u.unit_number,
        u.type as current_type,
        u.surface_area,
        u.rooms,
        u.floor,
        p.name as property_name,
        t.name as tenant_name
    FROM units u
    JOIN properties p ON u.property_id = p.id
    LEFT JOIN leases l ON l.unit_id = u.id AND (l.end_date IS NULL OR l.end_date > NOW())
    LEFT JOIN tenants t ON l.tenant_id = t.id
    ORDER BY p.name, u.unit_number
"""}).execute()

units = result.data

# Detection rules
def detect_type(unit):
    unit_num = (unit['unit_number'] or '').lower()
    tenant = (unit['tenant_name'] or '').lower()
    surface = unit['surface_area'] or 0
    rooms = unit['rooms'] or 0
    
    # Parking
    if any(kw in unit_num for kw in ['place', 'parking', 'garage', 'box']):
        return 'Parking'
    
    # Dépôt/Cave
    if any(kw in unit_num for kw in ['dépôt', 'depot', 'cave', 'lager']):
        return 'Dépôt'
    
    # Local technique
    if any(kw in unit_num for kw in ['local technique', 'local concierge', 'concierge']):
        return 'Local technique'
    
    # Magasin/Commerce
    if any(kw in unit_num for kw in ['magasin', 'commerce', 'laden', 'shop']):
        return 'Magasin'
    
    # Bureau
    if any(kw in unit_num for kw in ['bureau', 'büro', 'office']):
        return 'Bureau'
    
    # Si SA/Sàrl/GmbH dans tenant → probablement commercial
    if tenant and any(kw in tenant for kw in [' sa', ' sarl', ' sàrl', ' gmbh', ' ag']):
        # Si grande surface → Bureau, sinon Magasin
        if surface > 100:
            return 'Bureau'
        elif surface > 0:
            return 'Magasin'
    
    # Parking detection by metadata
    if surface == 0 and rooms == 0:
        return 'Parking'
    
    # Default: Appartement
    return 'Appartement'

# Analyze and prepare updates
updates = []
stats = {'Appartement': 0, 'Magasin': 0, 'Bureau': 0, 'Dépôt': 0, 'Parking': 0, 'Local technique': 0}

print("\n🔍 ANALYSE DES UNITÉS\n")
print(f"{'Propriété':<30} {'Unit':<25} {'Type actuel':<15} → {'Nouveau type':<15}")
print("=" * 100)

for unit in units:
    detected_type = detect_type(unit)
    current_type = unit['current_type'] or 'NULL'
    
    if detected_type != current_type:
        updates.append({
            'unit_id': unit['unit_id'],
            'new_type': detected_type,
            'unit_number': unit['unit_number'],
            'property': unit['property_name']
        })
        print(f"{unit['property_name']:<30} {unit['unit_number']:<25} {current_type:<15} → {detected_type:<15}")
    
    stats[detected_type] = stats.get(detected_type, 0) + 1

print("\n" + "=" * 100)
print(f"\n📊 STATISTIQUES:")
for type_name, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"   {type_name:<20}: {count:>4} unités")

print(f"\n🔄 {len(updates)} unités à mettre à jour")

if updates:
    response = input("\n❓ Appliquer ces changements? (oui/non): ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        print("\n⏳ Application des changements...")
        success_count = 0
        
        for update in updates:
            try:
                supabase.rpc('exec_sql', {'sql': f"""
                    UPDATE units 
                    SET type = '{update['new_type']}' 
                    WHERE id = '{update['unit_id']}'
                """}).execute()
                success_count += 1
            except Exception as e:
                print(f"❌ Erreur pour {update['unit_number']}: {e}")
        
        print(f"\n✅ {success_count}/{len(updates)} unités mises à jour!")
    else:
        print("\n❌ Changements annulés")
else:
    print("\n✅ Aucune correction nécessaire!")


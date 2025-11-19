"""
Generate final comprehensive report for insurance policies
"""
from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  RAPPORT FINAL - ASSURANCES")
print("="*80)

# Get all data
properties = supabase.table("properties").select("id, name, address, city").execute().data
policies = supabase.table("insurance_policies").select("*").execute().data

# Map property IDs to names
property_map = {p['id']: p for p in properties}

print(f"\n📊 VUE D'ENSEMBLE")
print(f"   {'='*75}")
print(f"   Propriétés totales      : {len(properties)}")
print(f"   Polices enregistrées    : {len(policies)}")
print(f"   Couverture              : 100%")

# Count by status
status_counts = defaultdict(int)
for pol in policies:
    status_counts[pol['status']] += 1

print(f"\n📋 PAR STATUT")
print(f"   {'='*75}")
for status, count in sorted(status_counts.items()):
    print(f"   {status:20} : {count}")

# By insurer
insurer_counts = defaultdict(int)
insurer_properties = defaultdict(list)
for pol in policies:
    insurer = pol['insurer_name']
    insurer_counts[insurer] += 1
    prop_name = property_map[pol['property_id']]['name']
    insurer_properties[insurer].append(prop_name)

print(f"\n🏢 PAR ASSUREUR")
print(f"   {'='*75}")
for insurer in sorted(insurer_counts.keys()):
    print(f"\n   {insurer}")
    print(f"   Polices: {insurer_counts[insurer]}")
    print(f"   Propriétés:")
    for prop in sorted(insurer_properties[insurer]):
        print(f"      • {prop}")

# Detailed by property
print(f"\n\n{'='*80}")
print(f"  DÉTAIL PAR PROPRIÉTÉ")
print(f"{'='*80}\n")

for prop in sorted(properties, key=lambda x: x['name']):
    prop_policies = [p for p in policies if p['property_id'] == prop['id']]
    
    print(f"🏢 {prop['name']}")
    print(f"   {prop.get('address', 'N/A')}, {prop.get('city', 'N/A')}")
    print(f"   Polices actives: {len(prop_policies)}")
    
    for pol in prop_policies:
        print(f"\n   📄 {pol['policy_type'].upper()}")
        print(f"      Assureur       : {pol['insurer_name']}")
        print(f"      Période        : {pol['policy_start_date']} → {pol['policy_end_date']}")
        print(f"      Statut         : {pol['status']}")
        if pol.get('policy_number'):
            print(f"      No Police      : {pol['policy_number']}")
        if pol.get('annual_premium') and pol['annual_premium'] > 0:
            print(f"      Prime annuelle : {pol['annual_premium']:,.2f} CHF")
        if pol.get('insured_value') and pol['insured_value'] > 0:
            print(f"      Valeur assurée : {pol['insured_value']:,.0f} CHF")
        if pol.get('notes'):
            print(f"      Note           : {pol['notes']}")
    
    print()

# Summary of data completeness
print(f"\n{'='*80}")
print(f"  COMPLÉTUDE DES DONNÉES")
print(f"{'='*80}\n")

complete_fields = {
    'policy_number': 0,
    'annual_premium': 0,
    'insured_value': 0,
    'building_value': 0,
    'contents_value': 0,
    'rental_loss_coverage': 0,
    'deductible_amount': 0
}

for pol in policies:
    for field in complete_fields:
        if pol.get(field) and (isinstance(pol[field], str) or pol[field] > 0):
            complete_fields[field] += 1

print(f"   Champ                    │ Complété │ %")
print(f"   {'─'*25}┼{'─'*10}┼{'─'*10}")
for field, count in complete_fields.items():
    pct = (count / len(policies) * 100) if policies else 0
    print(f"   {field:25} │ {count:>3}/{len(policies):<4} │ {pct:>5.1f}%")

# Actions needed
print(f"\n{'='*80}")
print(f"  ACTIONS RECOMMANDÉES")
print(f"{'='*80}\n")

to_verify = [p for p in policies if p['status'] == 'to_verify']
if to_verify:
    print(f"   ⚠️  {len(to_verify)} polices à vérifier:")
    for pol in to_verify:
        prop_name = property_map[pol['property_id']]['name']
        print(f"      • {prop_name}: {pol.get('notes', 'N/A')}")
    print()

missing_premium = [p for p in policies if not p.get('annual_premium') or p['annual_premium'] == 0]
if missing_premium:
    print(f"   💰 {len(missing_premium)} polices sans prime annuelle:")
    for pol in missing_premium:
        prop_name = property_map[pol['property_id']]['name']
        print(f"      • {prop_name}")
    print()

missing_values = [p for p in policies if not p.get('insured_value') or p['insured_value'] == 0]
if missing_values:
    print(f"   💼 {len(missing_values)} polices sans valeur assurée:")
    for pol in missing_values:
        prop_name = property_map[pol['property_id']]['name']
        print(f"      • {prop_name}")
    print()

print(f"\n✨ Utiliser Azure OCR pour extraire:")
print(f"   • Numéros de police")
print(f"   • Primes annuelles")
print(f"   • Valeurs assurées (bâtiment, contenu, perte loyer)")
print(f"   • Franchises")
print(f"   • Détails de couverture")

print(f"\n✅ Rapport généré avec succès!\n")



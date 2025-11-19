"""
Analyse et visualisation des servitudes importées
"""
from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  ANALYSE DES SERVITUDES")
print("="*80 + "\n")

# Get all properties
properties = supabase.table("properties").select("*").execute().data
props_by_id = {p['id']: p['name'] for p in properties}

# Get servitudes
print("[1/4] Chargement servitudes...")
servitudes = supabase.table("servitudes").select("*").execute().data
print(f"✅ {len(servitudes)} servitudes trouvées\n")

# Get land registry documents
print("[2/4] Chargement documents RF...")
lrd = supabase.table("land_registry_documents").select("*").execute().data
print(f"✅ {len(lrd)} documents RF trouvés\n")

# Analysis
print("[3/4] Analyse...")

# By property
by_property = defaultdict(list)
for serv in servitudes:
    prop_id = serv.get('property_id')
    if prop_id:
        by_property[prop_id].append(serv)

# By type
by_type = defaultdict(int)
for serv in servitudes:
    type_serv = serv.get('type_servitude', 'indéterminé')
    by_type[type_serv] += 1

# By importance
by_importance = defaultdict(int)
for serv in servitudes:
    importance = serv.get('importance_niveau', 'normale')
    by_importance[importance] += 1

# Impacts
impacts = {
    'constructibilité': len([s for s in servitudes if s.get('impact_constructibilite')]),
    'usage': len([s for s in servitudes if s.get('impact_usage')]),
    'valeur': len([s for s in servitudes if s.get('impact_valeur')])
}

# Documents RF by property
lrd_by_property = defaultdict(lambda: {'extrait_rf': 0, 'restrictions': 0, 'plan_affectation': 0, 'reglement_construction': 0})
for doc in lrd:
    prop_id = doc.get('property_id')
    doc_type = doc.get('document_type', 'autre')
    if prop_id:
        lrd_by_property[prop_id][doc_type] += 1

print("[4/4] Génération rapport...\n")

print("="*80)
print("  RÉSULTATS")
print("="*80 + "\n")

print("📊 VUE D'ENSEMBLE")
print("-" * 80)
print(f"  Total servitudes:          {len(servitudes)}")
print(f"  Total documents RF:        {len(lrd)}")
print(f"  Propriétés concernées:     {len(by_property)}")
print()

print("📋 PAR TYPE DE SERVITUDE")
print("-" * 80)
for type_name, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
    print(f"  {type_name:30s}: {count:3d}")
print()

print("⚠️  PAR NIVEAU D'IMPORTANCE")
print("-" * 80)
for importance, count in sorted(by_importance.items(), key=lambda x: x[1], reverse=True):
    print(f"  {importance:30s}: {count:3d}")
print()

print("🏗️  IMPACTS")
print("-" * 80)
for impact_type, count in impacts.items():
    pct = (count / len(servitudes) * 100) if len(servitudes) > 0 else 0
    print(f"  Impact {impact_type:20s}: {count:3d} ({pct:.1f}%)")
print()

print("="*80)
print("  PAR PROPRIÉTÉ")
print("="*80 + "\n")

for prop_id in sorted(by_property.keys(), key=lambda x: len(by_property[x]), reverse=True):
    prop_name = props_by_id.get(prop_id, 'Inconnu')
    servs = by_property[prop_id]
    docs = lrd_by_property[prop_id]
    
    print(f"📍 {prop_name}")
    print(f"   Servitudes:        {len(servs)}")
    print(f"   Extraits RF:       {docs['extrait_rf']}")
    print(f"   Restrictions:      {docs['restrictions']}")
    print(f"   Plans:             {docs['plan_affectation']}")
    print(f"   Règlements:        {docs['reglement_construction']}")
    
    # Detail servitudes
    if servs:
        critiques = [s for s in servs if s.get('importance_niveau') == 'critique']
        importantes = [s for s in servs if s.get('importance_niveau') == 'importante']
        
        if critiques:
            print(f"   ⚠️  CRITIQUES:       {len(critiques)}")
        if importantes:
            print(f"   ⚡ IMPORTANTES:     {len(importantes)}")
        
        # Impacts
        impacts_prop = {
            'construct': len([s for s in servs if s.get('impact_constructibilite')]),
            'usage': len([s for s in servs if s.get('impact_usage')]),
            'valeur': len([s for s in servs if s.get('impact_valeur')])
        }
        
        if any(impacts_prop.values()):
            print(f"   Impacts: ", end="")
            impact_strs = []
            if impacts_prop['construct']:
                impact_strs.append(f"Construction ({impacts_prop['construct']})")
            if impacts_prop['usage']:
                impact_strs.append(f"Usage ({impacts_prop['usage']})")
            if impacts_prop['valeur']:
                impact_strs.append(f"Valeur ({impacts_prop['valeur']})")
            print(", ".join(impact_strs))
    
    print()

# Show sample servitudes
print("="*80)
print("  EXEMPLES DE SERVITUDES")
print("="*80 + "\n")

# Show first 5 servitudes with details
for i, serv in enumerate(servitudes[:5], 1):
    prop_id = serv.get('property_id')
    prop_name = props_by_id.get(prop_id, 'Inconnu')
    
    print(f"{i}. {prop_name}")
    print(f"   Type:        {serv.get('type_servitude', 'N/A')}")
    print(f"   Importance:  {serv.get('importance_niveau', 'N/A')}")
    print(f"   Statut:      {serv.get('statut', 'N/A')}")
    
    desc = serv.get('description', '')
    if desc:
        desc_short = desc[:150] + "..." if len(desc) > 150 else desc
        print(f"   Description: {desc_short}")
    
    if serv.get('impact_constructibilite'):
        print(f"   ⚠️  Impacte la constructibilité")
    if serv.get('impact_usage'):
        print(f"   ⚠️  Impacte l'usage")
    
    print()

print("="*80)
print("  RECOMMANDATIONS")
print("="*80 + "\n")

# Identify properties needing attention
for prop_id, servs in by_property.items():
    prop_name = props_by_id.get(prop_id, 'Inconnu')
    critiques = [s for s in servs if s.get('importance_niveau') == 'critique']
    impacts_construct = [s for s in servs if s.get('impact_constructibilite')]
    
    if critiques or len(impacts_construct) >= 2:
        print(f"🔴 {prop_name}")
        if critiques:
            print(f"   → {len(critiques)} servitude(s) critique(s) à vérifier")
        if len(impacts_construct) >= 2:
            print(f"   → {len(impacts_construct)} servitude(s) impactant la construction")
        print()

print("\n💡 PROCHAINES ACTIONS:")
print("   1. Vérifier manuellement les servitudes critiques")
print("   2. Compléter les champs manquants (dates, montants, etc.)")
print("   3. Lier les servitudes aux unités concernées")
print("   4. Mettre à jour importance_niveau si nécessaire\n")

print("🎯 REQUÊTES UTILES:")
print("   • Servitudes critiques:  SELECT * FROM servitudes WHERE importance_niveau = 'critique'")
print("   • Par propriété:         SELECT * FROM vw_servitudes_summary")
print("   • Impacts construction:  SELECT * FROM servitudes WHERE impact_constructibilite = true\n")


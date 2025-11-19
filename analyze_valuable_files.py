"""
Analyze recent files to identify valuable data for import
"""
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

print("="*80)
print("  ANALYSE FICHIERS RÉCENTS - VALEUR POUR IMPORT")
print("="*80)

# Define file categories
categories = {
    'États locatifs': [],
    'Rapports DCF/CBRE': [],
    'Polices assurance': [],
    'Mandats de gérance': [],
    'Compte de résultat': [],
    'Plans': [],
    'Autres Excel': []
}

# Scan recent files
root = Path('.')
cutoff_date = datetime.now() - timedelta(days=30)

print(f"\n📅 Fichiers modifiés depuis: {cutoff_date.strftime('%d.%m.%Y')}\n")

for file_path in root.rglob('*'):
    if not file_path.is_file():
        continue
    
    if file_path.stat().st_mtime < cutoff_date.timestamp():
        continue
    
    name_lower = file_path.name.lower()
    
    # Categorize
    if 'etat_locatif' in name_lower or 'el ' in name_lower:
        categories['États locatifs'].append(file_path)
    elif 'dcf' in name_lower or 'cbre' in name_lower:
        categories['Rapports DCF/CBRE'].append(file_path)
    elif 'police' in name_lower and 'assurance' not in name_lower:
        categories['Polices assurance'].append(file_path)
    elif 'mandat' in name_lower and 'gérance' in name_lower:
        categories['Mandats de gérance'].append(file_path)
    elif 'compte' in name_lower and 'resultat' in name_lower:
        categories['Compte de résultat'].append(file_path)
    elif file_path.suffix.lower() == '.pdf' and any(x in name_lower for x in ['plan', 'etage', 'type']):
        categories['Plans'].append(file_path)
    elif file_path.suffix.lower() in ['.xlsx', '.xls'] and file_path.name not in ['EL Be Capital 11.12.24.xlsx']:
        categories['Autres Excel'].append(file_path)

# Analyze each category
print("📊 CATÉGORIES IDENTIFIÉES:\n")

for category, files in categories.items():
    if not files:
        continue
    
    print(f"\n{'='*80}")
    print(f"  {category.upper()} ({len(files)} fichiers)")
    print(f"{'='*80}")
    
    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
        size_mb = f.stat().st_size / (1024*1024)
        mod_date = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"\n   📄 {f.name}")
        print(f"      Taille: {size_mb:.2f} MB")
        print(f"      Modifié: {mod_date.strftime('%d.%m.%Y %H:%M')}")
        
        # Try to analyze Excel files
        if f.suffix.lower() in ['.xlsx', '.xls']:
            try:
                xl = pd.ExcelFile(f)
                print(f"      Feuilles: {', '.join(xl.sheet_names[:3])}")
                
                df = pd.read_excel(f, sheet_name=0, nrows=5)
                print(f"      Colonnes: {len(df.columns)}")
                
            except Exception as e:
                print(f"      ⚠️ Erreur lecture: {str(e)[:50]}")

# Recommendations
print(f"\n\n{'='*80}")
print(f"  RECOMMANDATIONS D'IMPORT")
print(f"{'='*80}\n")

recommendations = []

if categories['États locatifs']:
    recommendations.append({
        'priority': 1,
        'category': 'États locatifs',
        'files': len(categories['États locatifs']),
        'value': 'HAUTE',
        'reason': 'Données de revenus locatifs actualisées par propriété',
        'target_table': 'leases (mise à jour rent_net, charges)',
        'action': 'Comparer avec données existantes et mettre à jour les loyers'
    })

if categories['Compte de résultat']:
    recommendations.append({
        'priority': 2,
        'category': 'Compte de résultat',
        'files': len(categories['Compte de résultat']),
        'value': 'HAUTE',
        'reason': 'Vue financière consolidée du portefeuille',
        'target_table': 'Nouvelle table: financial_statements',
        'action': 'Créer table pour P&L, extraire revenus/charges/résultat'
    })

if categories['Polices assurance']:
    recommendations.append({
        'priority': 3,
        'category': 'Polices assurance',
        'files': len(categories['Polices assurance']),
        'value': 'MOYENNE',
        'reason': 'Informations assurances par propriété',
        'target_table': 'Nouvelle table: insurance_policies',
        'action': 'Extraire: assureur, montant prime, dates, couverture'
    })

if categories['Rapports DCF/CBRE']:
    recommendations.append({
        'priority': 4,
        'category': 'Rapports DCF/CBRE',
        'files': len(categories['Rapports DCF/CBRE']),
        'value': 'MOYENNE',
        'reason': 'Valorisations et projections financières',
        'target_table': 'Nouvelle table: valuations',
        'action': 'Extraire: valeur expertisée, taux capitalisation, cash-flows'
    })

if categories['Plans']:
    recommendations.append({
        'priority': 5,
        'category': 'Plans architecturaux',
        'files': len(categories['Plans']),
        'value': 'BASSE',
        'reason': 'Plans techniques des étages',
        'target_table': 'documents (upload as-is)',
        'action': 'Stocker comme documents de référence'
    })

# Sort by priority
for rec in sorted(recommendations, key=lambda x: x['priority']):
    print(f"{rec['priority']}. {rec['category']} - VALEUR {rec['value']}")
    print(f"   📁 Fichiers: {rec['files']}")
    print(f"   💡 Raison: {rec['reason']}")
    print(f"   🎯 Cible: {rec['target_table']}")
    print(f"   ⚡ Action: {rec['action']}")
    print()

print(f"{'='*80}")
print(f"  PROCHAINE ÉTAPE RECOMMANDÉE")
print(f"{'='*80}\n")

if recommendations:
    top = recommendations[0]
    print(f"🏆 PRIORITÉ #1: {top['category']}")
    print(f"\n   Fichiers identifiés: {top['files']}")
    print(f"   Valeur business: {top['value']}")
    print(f"   Action: {top['action']}")
    print(f"\n   ➡️  Voulez-vous que je commence par importer ces données?")



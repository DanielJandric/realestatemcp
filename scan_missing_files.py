"""
Scan OneDriveExport and identify files that should be imported but aren't in the database yet
"""
from supabase import create_client
from pathlib import Path
from collections import defaultdict

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

ROOT_DIR = Path(r"C:\OneDriveExport")

print("="*80)
print("  SCAN FICHIERS MANQUANTS - OneDriveExport")
print("="*80)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Categories of valuable files
VALUABLE_CATEGORIES = {
    'Baux/Leases': {
        'patterns': ['bail', 'baux', 'lease', 'contrat de bail', 'mietvertrag', 'wohnung'],
        'extensions': ['.pdf', '.docx', '.doc'],
        'min_size': 10_000  # >10KB
    },
    'Assurances': {
        'patterns': ['assurance', 'police', 'insurance', 'versicherung'],
        'extensions': ['.pdf', '.docx'],
        'min_size': 5_000
    },
    'Maintenance': {
        'patterns': ['maintenance', 'entretien', 'contrat', 'wartung'],
        'extensions': ['.pdf', '.xlsx', '.xls', '.docx'],
        'min_size': 1_000
    },
    'Sinistres/Litiges': {
        'patterns': ['sinistre', 'litige', 'incident', 'dommage', 'reclamation', 'dispute'],
        'extensions': ['.pdf', '.docx', '.xlsx'],
        'min_size': 1_000
    },
    'Factures': {
        'patterns': ['facture', 'invoice', 'rechnung'],
        'extensions': ['.pdf', '.xlsx', '.xls'],
        'min_size': 1_000
    },
    'Financiers': {
        'patterns': ['compte', 'resultat', 'bilan', 'financier', 'decompte'],
        'extensions': ['.xlsx', '.xls', '.pdf'],
        'min_size': 5_000
    },
    'Etats Locatifs': {
        'patterns': ['etat locatif', 'etat des lieux', 'inventaire'],
        'extensions': ['.pdf', '.xlsx', '.docx'],
        'min_size': 5_000
    },
    'Plans/Expertise': {
        'patterns': ['plan', 'expertise', 'evaluation', 'valuation'],
        'extensions': ['.pdf', '.dwg'],
        'min_size': 10_000
    }
}

# Exclusions
EXCLUDE_PATTERNS = [
    '__pycache__', '.pyc', '.log', '.tmp', '.old',
    'test_', 'debug_', 'check_', 'analyze_', 'inspect_',
    'import_', 'migrate_', 'extract_', 'sync_',
    'RAPPORT_', 'STATUS', 'FINAL', '.md', '.sql', '.txt',
    'Incremental', 'mcp_', 'corruption'
]

def should_exclude(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path).lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in path_str:
            return True
    return False

def categorize_file(file_path):
    """Determine category of file"""
    name_lower = file_path.name.lower()
    ext_lower = file_path.suffix.lower()
    
    for category, criteria in VALUABLE_CATEGORIES.items():
        # Check extension
        if ext_lower not in criteria['extensions']:
            continue
        
        # Check size
        try:
            if file_path.stat().st_size < criteria['min_size']:
                continue
        except:
            continue
        
        # Check patterns
        for pattern in criteria['patterns']:
            if pattern in name_lower or pattern in str(file_path.parent).lower():
                return category
    
    return None

# Scan all files
print("\n📁 Scan en cours...")
all_files = defaultdict(list)
total_scanned = 0

for file_path in ROOT_DIR.rglob('*'):
    if not file_path.is_file():
        continue
    
    total_scanned += 1
    
    if should_exclude(file_path):
        continue
    
    category = categorize_file(file_path)
    if category:
        all_files[category].append(file_path)

print(f"✅ {total_scanned:,} fichiers scannés\n")

# Display found files by category
print("="*80)
print("  FICHIERS IDENTIFIÉS PAR CATÉGORIE")
print("="*80)

total_valuable = 0
for category, files in sorted(all_files.items()):
    print(f"\n📂 {category}: {len(files)} fichiers")
    total_valuable += len(files)
    
    # Show first 5 examples
    for file_path in files[:5]:
        size_kb = file_path.stat().st_size / 1024
        rel_path = file_path.relative_to(ROOT_DIR)
        print(f"   • {rel_path} ({size_kb:.1f} KB)")
    
    if len(files) > 5:
        print(f"   ... et {len(files) - 5} autres")

print(f"\n📊 TOTAL: {total_valuable} fichiers à potentiellement importer")

# Check what's already in database
print(f"\n{'='*80}")
print(f"  VÉRIFICATION BASE DE DONNÉES")
print(f"{'='*80}\n")

# Check existing data
tables_to_check = {
    'leases': 'Baux/Leases',
    'insurance_policies': 'Assurances',
    'maintenance_contracts': 'Maintenance',
    'incidents': 'Sinistres/Litiges',
    'financial_statements': 'Financiers'
}

for table, category in tables_to_check.items():
    try:
        result = supabase.table(table).select("count", count="exact").execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        file_count = len(all_files.get(category, []))
        
        status = "✅" if count > 0 else "❌"
        print(f"{status} {table:30} : {count:4} records | {file_count:4} fichiers trouvés")
        
        if file_count > count:
            print(f"   ⚠️  {file_count - count} fichiers potentiellement manquants")
    except Exception as e:
        print(f"❌ {table:30} : Erreur - {str(e)}")

# Generate import recommendations
print(f"\n{'='*80}")
print(f"  RECOMMANDATIONS D'IMPORT")
print(f"{'='*80}\n")

recommendations = []

# Baux
if len(all_files.get('Baux/Leases', [])) > 0:
    recommendations.append({
        'priority': 1,
        'category': 'Baux/Leases',
        'count': len(all_files['Baux/Leases']),
        'script': 'extract_all_leases.py (déjà fait ?)',
        'table': 'leases'
    })

# Assurances
if len(all_files.get('Assurances', [])) > 0:
    recommendations.append({
        'priority': 2,
        'category': 'Assurances',
        'count': len(all_files['Assurances']),
        'script': 'import_insurance_policies.py (déjà fait ?)',
        'table': 'insurance_policies'
    })

# Maintenance
if len(all_files.get('Maintenance', [])) > 0:
    recommendations.append({
        'priority': 3,
        'category': 'Maintenance',
        'count': len(all_files['Maintenance']),
        'script': 'import_maintenance_contracts.py (déjà fait ?)',
        'table': 'maintenance_contracts'
    })

# Sinistres/Litiges
if len(all_files.get('Sinistres/Litiges', [])) > 0:
    recommendations.append({
        'priority': 4,
        'category': 'Sinistres/Litiges',
        'count': len(all_files['Sinistres/Litiges']),
        'script': 'import_sinistres_litiges.py (déjà fait ?)',
        'table': 'incidents'
    })

# Financiers
if len(all_files.get('Financiers', [])) > 0:
    recommendations.append({
        'priority': 5,
        'category': 'Financiers',
        'count': len(all_files['Financiers']),
        'script': 'import_financial_statements.py (déjà fait ?)',
        'table': 'financial_statements'
    })

# Autres
other_categories = set(all_files.keys()) - set([r['category'] for r in recommendations])
for category in other_categories:
    recommendations.append({
        'priority': 10,
        'category': category,
        'count': len(all_files[category]),
        'script': 'À créer',
        'table': 'documents (générique)'
    })

# Sort and display
for rec in sorted(recommendations, key=lambda x: x['priority']):
    priority_label = "🔴 HAUTE" if rec['priority'] <= 2 else "🟡 MOYENNE" if rec['priority'] <= 5 else "🟢 BASSE"
    print(f"{priority_label} - {rec['category']}")
    print(f"   Fichiers: {rec['count']}")
    print(f"   Table: {rec['table']}")
    print(f"   Script: {rec['script']}\n")

# Save detailed list
output_file = ROOT_DIR / "fichiers_a_importer.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("FICHIERS À IMPORTER\n")
    f.write("="*80 + "\n\n")
    
    for category, files in sorted(all_files.items()):
        f.write(f"\n{category} ({len(files)} fichiers)\n")
        f.write("-" * 80 + "\n")
        for file_path in files:
            rel_path = file_path.relative_to(ROOT_DIR)
            size_kb = file_path.stat().st_size / 1024
            f.write(f"{rel_path} ({size_kb:.1f} KB)\n")

print(f"💾 Liste détaillée sauvée: fichiers_a_importer.txt\n")

print("="*80)
print("  PROCHAINES ÉTAPES")
print("="*80)
print("""
1. Vérifier si imports déjà faits (check tables Supabase)
2. Pour chaque catégorie manquante:
   - Vérifier si script existe
   - L'exécuter ou en créer un nouveau
3. Une fois imports complets, lancer embeddings

📋 Voulez-vous que je crée un script d'import manquant ?
""")



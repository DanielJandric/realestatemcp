"""
Analyze all 3716 files in OneDriveExport to determine value for embeddings
"""
from pathlib import Path
from collections import defaultdict
import os

print("="*80)
print("  ANALYSE COMPLÈTE DES 3716 FICHIERS")
print("="*80)

root_dir = Path(r"C:\OneDriveExport")

# Statistics
stats = {
    'total_files': 0,
    'total_size': 0,
    'by_extension': defaultdict(lambda: {'count': 0, 'size': 0}),
    'by_category': defaultdict(lambda: {'count': 0, 'size': 0, 'files': []}),
    'by_directory': defaultdict(lambda: {'count': 0, 'size': 0})
}

# Categories for embedding value
categories = {
    'HAUTE_VALEUR': {  # High value for embeddings
        'patterns': [
            'bail', 'baux', 'lease', 'contrat', 'contract',
            'facture', 'invoice', 'devis', 'quote',
            'rapport', 'report', 'expertise', 'evaluation',
            'assurance', 'insurance', 'police',
            'sinistre', 'incident', 'litige', 'dispute',
            'maintenance', 'entretien', 'reparation'
        ],
        'extensions': ['.pdf', '.docx', '.doc']
    },
    'VALEUR_MOYENNE': {  # Medium value
        'patterns': [
            'etat', 'locatif', 'locative',
            'compte', 'resultat', 'financier',
            'budget', 'prevision'
        ],
        'extensions': ['.xlsx', '.xls', '.csv']
    },
    'FAIBLE_VALEUR': {  # Low value
        'patterns': [],
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    },
    'AUCUNE_VALEUR': {  # No value for embeddings
        'patterns': [],
        'extensions': ['.py', '.sql', '.md', '.txt', '.json', '.log', '.tmp']
    }
}

def categorize_file(file_path):
    """Categorize file for embedding value"""
    name_lower = file_path.name.lower()
    ext_lower = file_path.suffix.lower()
    
    # Check high value
    for pattern in categories['HAUTE_VALEUR']['patterns']:
        if pattern in name_lower:
            return 'HAUTE_VALEUR'
    if ext_lower in categories['HAUTE_VALEUR']['extensions']:
        # PDF but not high-value name? Check size (small PDFs might be templates)
        if file_path.stat().st_size > 50_000:  # >50KB
            return 'HAUTE_VALEUR'
    
    # Check medium value
    for pattern in categories['VALEUR_MOYENNE']['patterns']:
        if pattern in name_lower:
            return 'VALEUR_MOYENNE'
    if ext_lower in categories['VALEUR_MOYENNE']['extensions']:
        return 'VALEUR_MOYENNE'
    
    # Check low value
    if ext_lower in categories['FAIBLE_VALEUR']['extensions']:
        return 'FAIBLE_VALEUR'
    
    # Check no value
    if ext_lower in categories['AUCUNE_VALEUR']['extensions']:
        return 'AUCUNE_VALEUR'
    
    return 'NON_CATEGORISE'

print("\n🔍 Scanning tous les fichiers...\n")

for file_path in root_dir.rglob('*'):
    if file_path.is_file():
        try:
            size = file_path.stat().st_size
            ext = file_path.suffix.lower()
            
            stats['total_files'] += 1
            stats['total_size'] += size
            
            # By extension
            stats['by_extension'][ext]['count'] += 1
            stats['by_extension'][ext]['size'] += size
            
            # By category
            category = categorize_file(file_path)
            stats['by_category'][category]['count'] += 1
            stats['by_category'][category]['size'] += size
            
            # Store samples
            if len(stats['by_category'][category]['files']) < 5:
                stats['by_category'][category]['files'].append(str(file_path.relative_to(root_dir)))
            
            # By directory (top level)
            try:
                top_dir = file_path.relative_to(root_dir).parts[0]
                stats['by_directory'][top_dir]['count'] += 1
                stats['by_directory'][top_dir]['size'] += size
            except:
                pass
                
        except Exception as e:
            pass

print("="*80)
print("  RÉSULTATS")
print("="*80)

# Overall stats
print(f"\n📊 STATISTIQUES GLOBALES:")
print(f"   Total fichiers          : {stats['total_files']:>10,}")
print(f"   Taille totale           : {stats['total_size'] / (1024**3):>10,.2f} GB")
print(f"   Taille moyenne/fichier  : {stats['total_size'] / stats['total_files'] / 1024:>10,.1f} KB")

# By category (MOST IMPORTANT)
print(f"\n{'='*80}")
print(f"🎯 PAR CATÉGORIE (VALEUR POUR EMBEDDINGS)")
print(f"{'='*80}\n")

category_order = ['HAUTE_VALEUR', 'VALEUR_MOYENNE', 'FAIBLE_VALEUR', 'AUCUNE_VALEUR', 'NON_CATEGORISE']

for category in category_order:
    if category in stats['by_category']:
        data = stats['by_category'][category]
        count = data['count']
        size_gb = data['size'] / (1024**3)
        pct = (count / stats['total_files'] * 100)
        
        emoji = {
            'HAUTE_VALEUR': '🟢',
            'VALEUR_MOYENNE': '🟡',
            'FAIBLE_VALEUR': '🟠',
            'AUCUNE_VALEUR': '🔴',
            'NON_CATEGORISE': '⚪'
        }.get(category, '⚪')
        
        print(f"{emoji} {category:20}")
        print(f"   Fichiers  : {count:>6,} ({pct:>5.1f}%)")
        print(f"   Taille    : {size_gb:>6.2f} GB")
        print(f"   Exemples  :")
        for sample in data['files'][:3]:
            print(f"      • {sample}")
        print()

# By extension (top 15)
print(f"{'='*80}")
print(f"📄 PAR TYPE DE FICHIER (TOP 15)")
print(f"{'='*80}\n")

sorted_ext = sorted(stats['by_extension'].items(), key=lambda x: x[1]['count'], reverse=True)[:15]

for ext, data in sorted_ext:
    ext_display = ext if ext else '[no extension]'
    count = data['count']
    size_mb = data['size'] / (1024**2)
    pct = (count / stats['total_files'] * 100)
    print(f"   {ext_display:15} : {count:>5,} fichiers ({pct:>4.1f}%) - {size_mb:>8,.1f} MB")

# By directory (top 10)
print(f"\n{'='*80}")
print(f"📁 PAR DOSSIER PRINCIPAL (TOP 10)")
print(f"{'='*80}\n")

sorted_dirs = sorted(stats['by_directory'].items(), key=lambda x: x[1]['count'], reverse=True)[:10]

for dir_name, data in sorted_dirs:
    count = data['count']
    size_mb = data['size'] / (1024**2)
    pct = (count / stats['total_files'] * 100)
    print(f"   {dir_name:40} : {count:>5,} ({pct:>4.1f}%) - {size_mb:>8,.1f} MB")

# RECOMMENDATION
print(f"\n{'='*80}")
print(f"💡 RECOMMANDATION")
print(f"{'='*80}\n")

high_value = stats['by_category']['HAUTE_VALEUR']['count']
medium_value = stats['by_category']['VALEUR_MOYENNE']['count']
low_value = stats['by_category']['FAIBLE_VALEUR']['count']
no_value = stats['by_category']['AUCUNE_VALEUR']['count']

total_valuable = high_value + medium_value

print(f"✅ FICHIERS À EMBEDDER:")
print(f"   Haute valeur (PDFs contrats, baux, rapports)  : {high_value:>6,}")
print(f"   Valeur moyenne (Excel financiers)             : {medium_value:>6,}")
print(f"   TOTAL RECOMMANDÉ                               : {total_valuable:>6,}")

print(f"\n❌ FICHIERS À EXCLURE:")
print(f"   Images/Plans (faible valeur)                   : {low_value:>6,}")
print(f"   Scripts/Logs (aucune valeur)                   : {no_value:>6,}")

# Cost estimation
if total_valuable > 0:
    high_size = stats['by_category']['HAUTE_VALEUR']['size']
    medium_size = stats['by_category']['VALEUR_MOYENNE']['size']
    total_size = high_size + medium_size
    
    # Estimate tokens (rough: 1MB text ≈ 300K tokens, PDF ≈ 150K tokens)
    estimated_tokens = (high_size / (1024**2)) * 150_000 + (medium_size / (1024**2)) * 100_000
    
    # OpenAI embedding cost: $0.13 per 1M tokens
    embedding_cost = (estimated_tokens / 1_000_000) * 0.13
    
    # Storage cost (Supabase: ~0.125$ per GB per month)
    storage_cost_monthly = (total_size / (1024**3)) * 0.125
    
    print(f"\n💰 ESTIMATION COÛTS:")
    print(f"   Taille à embedder                              : {total_size / (1024**3):>6.2f} GB")
    print(f"   Tokens estimés                                 : {estimated_tokens / 1_000_000:>6.1f}M")
    print(f"   Coût embeddings (one-time)                     : {embedding_cost:>6.2f} USD")
    print(f"   Coût stockage (mensuel)                        : {storage_cost_monthly:>6.2f} USD")

print(f"\n🎯 STRATÉGIE RECOMMANDÉE:")
print(f"   1. Commencer par HAUTE_VALEUR uniquement ({high_value:,} fichiers)")
print(f"   2. Tester utilité avec cas d'usage réels")
print(f"   3. Si utile, étendre à VALEUR_MOYENNE")
print(f"   4. JAMAIS embedder images/scripts (perte argent/temps)")

print(f"\n✅ Analyse terminée!\n")



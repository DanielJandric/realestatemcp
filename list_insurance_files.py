"""
List all insurance policy files
"""
from pathlib import Path
import re

print("="*80)
print("  LISTE DES POLICES D'ASSURANCE")
print("="*80)

# Search for insurance files
insurance_files = []

# Search patterns
patterns = [
    '*police*.pdf',
    '*assurance*.pdf',
    '*Police*.pdf',
    '*Assurance*.pdf'
]

for pattern in patterns:
    for f in Path('.').rglob(pattern):
        if f.is_file() and f not in insurance_files:
            insurance_files.append(f)

# Remove duplicates
insurance_files = list(set(insurance_files))

print(f"\n📄 {len(insurance_files)} fichiers trouvés\n")

# Categorize by property
by_property = {}

for f in sorted(insurance_files, key=lambda x: x.stat().st_mtime, reverse=True):
    name_lower = f.name.lower()
    
    # Try to identify property
    property_name = 'Unknown'
    
    if 'be capital' in name_lower and 'sion' in name_lower:
        property_name = 'Gare 28 / St-Hubert (Sion)'
    elif 'be capital' in name_lower and 'aigle' in name_lower:
        property_name = "Pre d'Emoz (Aigle)"
    elif 'audacia' in name_lower and 'martigny' in name_lower:
        property_name = 'Gare 8-10 / Place Centrale 3 (Martigny)'
    elif 'gare' in name_lower:
        property_name = 'Gare'
    elif 'centrale' in name_lower:
        property_name = 'Place Centrale'
    elif 'pratifori' in name_lower or 'patrifori' in name_lower:
        property_name = 'Pratifori'
    elif 'banque' in name_lower:
        property_name = 'Banque 4'
    
    if property_name not in by_property:
        by_property[property_name] = []
    
    by_property[property_name].append(f)

# Display by property
for prop, files in sorted(by_property.items()):
    print(f"\n{'='*80}")
    print(f"  {prop.upper()}")
    print(f"{'='*80}")
    
    for f in files:
        size_mb = f.stat().st_size / (1024*1024)
        print(f"\n   📄 {f.name}")
        print(f"      Taille: {size_mb:.2f} MB")
        print(f"      Chemin: {f.parent}")
        
        # Try to extract dates from filename
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', f.name)
        if date_match:
            print(f"      Date: {date_match.group(1)}")
        
        # Try to extract period
        period_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*au\s*(\d{2}\.\d{2}\.\d{4})', f.name)
        if period_match:
            print(f"      Période: {period_match.group(1)} au {period_match.group(2)}")

# Summary
print(f"\n{'='*80}")
print(f"  RÉSUMÉ")
print(f"{'='*80}\n")

print(f"Total fichiers: {len(insurance_files)}")
print(f"Propriétés identifiées: {len(by_property)}")

print(f"\nPar propriété:")
for prop, files in sorted(by_property.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"   {prop:40}: {len(files)} fichier(s)")

print(f"\n📋 Fichiers principaux identifiés:")
main_policies = [f for f in insurance_files if 'police du' in f.name.lower() and f.stat().st_size > 100000]
for f in main_policies[:10]:
    print(f"   - {f.name}")



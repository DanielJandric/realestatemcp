"""
Inspect maintenance contract Excel files structure
"""
import pandas as pd
from pathlib import Path
import sys

print("="*80)
print("  ANALYSE FICHIERS CONTRATS D'ENTRETIEN")
print("="*80)

# List of maintenance files
files = [
    r"Incremental1\Gare 8-10 - Martigny - DD\09. Contrats de maintenance\Gare 8-10 Martigny_contrats d'entretien_Màj au 03.10.2024.xlsx",
    r"Incremental1\09. Contrats de maintenance\Becapital_contrats d'entretien_Gare 28 Sion_Màj au 05.09.2024.xlsx",
    r"Incremental1\Centrale 3 - Martigny - DD\09. Contrats de maintenance\Audacia_contrats d'entretien_Pl. Centrale 3 à Martigny_MàJ au 05.09.2024.xlsx",
    r"Incremental1\Grande-Avenue 6 - Chippis - DD\08. Contrats de maintenance\Audacia_Contrats d'entretien_GrandeAvenue6 Chippis_07.10.2025.xlsx",
    r"Pratifori 5-7 - Sion - DD\09. Contrats de maintenance\Pratifori 5-7_contrats d'entretien_Màj au 09.10.2025.xlsx",
    r"Banque 4 - Fribourg - DD\09. Contrats de maintenance\Banque 4 Fribourg_contrats d'entretien_Màj au 16.07.2025 (PAS ENVOYE).xlsx"
]

print(f"\n📄 Fichiers trouvés: {len(files)}\n")

for i, file_path in enumerate(files, 1):
    full_path = Path(file_path)
    
    if not full_path.exists():
        print(f"\n{i}. ❌ FICHIER NON TROUVÉ: {full_path.name}")
        continue
    
    print(f"\n{i}. {full_path.name}")
    print(f"   {'='*70}")
    
    try:
        # Try to read Excel
        xl = pd.ExcelFile(full_path)
        print(f"   Feuilles: {xl.sheet_names}")
        
        # Read first sheet
        df = pd.read_excel(full_path, sheet_name=0)
        
        print(f"   Lignes: {len(df)}")
        print(f"   Colonnes ({len(df.columns)}):")
        for col in df.columns:
            print(f"      - {col}")
        
        # Show first 2 rows
        if len(df) > 0:
            print(f"\n   📋 APERÇU (2 premières lignes):")
            print(f"   {'-'*70}")
            for idx, row in df.head(2).iterrows():
                print(f"\n   Ligne {idx+1}:")
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val):
                        val_str = str(val)[:60]
                        print(f"      {col:30}: {val_str}")
                        
    except Exception as e:
        print(f"   ❌ Erreur lecture: {str(e)[:100]}")

print(f"\n{'='*80}")
print(f"  ANALYSE TERMINÉE")
print(f"{'='*80}")



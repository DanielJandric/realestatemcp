"""
Detailed inspection of maintenance files with proper header detection
"""
import pandas as pd
from pathlib import Path

print("="*80)
print("  ANALYSE DÉTAILLÉE CONTRATS D'ENTRETIEN")
print("="*80)

# Test with first file
file_path = Path(r"Incremental1\Gare 8-10 - Martigny - DD\09. Contrats de maintenance\Gare 8-10 Martigny_contrats d'entretien_Màj au 03.10.2024.xlsx")

print(f"\n📄 Fichier test: {file_path.name}\n")

# Try different header rows
for header_row in range(0, 6):
    print(f"\n{'='*70}")
    print(f"Tentative avec header={header_row}")
    print(f"{'='*70}")
    
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=header_row)
        
        print(f"Colonnes: {list(df.columns)}")
        print(f"Lignes: {len(df)}")
        
        # Show first valid row
        if len(df) > 0:
            first_row = df.iloc[0]
            print(f"\nPremière ligne de données:")
            for col in df.columns:
                val = first_row[col]
                if pd.notna(val):
                    print(f"   {col:30}: {str(val)[:60]}")
        
        # Check if this looks like good headers
        col_names = [str(c).lower() for c in df.columns]
        keywords = ['prestataire', 'cout', 'coût', 'description', 'date', 'debut', 'début', 'fin']
        matches = sum(1 for kw in keywords if any(kw in cn for cn in col_names))
        
        if matches >= 3:
            print(f"\n✅ BON CANDIDAT ({matches} keywords trouvés)")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)[:100]}")

# Now read properly with correct header
print(f"\n\n{'='*80}")
print(f"LECTURE AVEC BON HEADER")
print(f"{'='*80}\n")

try:
    # Usually header is at row 3 or 4
    df = pd.read_excel(file_path, sheet_name=0, header=4)
    
    print(f"📊 Structure finale:")
    print(f"   Lignes: {len(df)}")
    print(f"   Colonnes: {list(df.columns)}\n")
    
    # Show first 3 rows with all columns
    print(f"📋 Premières lignes (données réelles):\n")
    
    for idx in range(min(3, len(df))):
        row = df.iloc[idx]
        print(f"Ligne {idx+1}:")
        for col in df.columns:
            val = row[col]
            if pd.notna(val) and str(val).strip() != '':
                print(f"   {col:35}: {str(val)[:70]}")
        print()
        
except Exception as e:
    print(f"❌ Erreur: {e}")



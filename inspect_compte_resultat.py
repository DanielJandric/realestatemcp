"""
Inspect Compte de Résultat file to see structure
"""
import pandas as pd
from pathlib import Path

print("="*80)
print("  INSPECTION COMPTE DE RÉSULTAT")
print("="*80)

file_path = Path(r"Copie de Comptedersultat-436-BeCapitalSABaar20241211-1573736-wpg4qn.xlsx")

if not file_path.exists():
    print(f"\n❌ Fichier non trouvé: {file_path}")
    print("\nRecherche alternative...")
    
    # Search for the file
    for f in Path('.').rglob('*Comptedersultat*.xlsx'):
        print(f"   Trouvé: {f}")
        file_path = f
        break

if file_path.exists():
    print(f"\n📄 Fichier: {file_path.name}\n")
    
    try:
        # Read Excel file
        xl = pd.ExcelFile(file_path)
        print(f"📋 Feuilles: {xl.sheet_names}\n")
        
        # Read first sheet
        df = pd.read_excel(file_path, sheet_name=0)
        
        print(f"📊 Structure:")
        print(f"   Lignes: {len(df)}")
        print(f"   Colonnes: {len(df.columns)}")
        print(f"\n   Noms des colonnes:")
        for i, col in enumerate(df.columns, 1):
            print(f"      {i}. {col}")
        
        # Show first rows
        print(f"\n📋 APERÇU (10 premières lignes):\n")
        print(df.head(10).to_string())
        
        # Check if by property
        print(f"\n\n🔍 ANALYSE:")
        
        # Look for property names in columns or data
        property_keywords = ['gare', 'centrale', 'pratifori', 'banque', 'hubert', 'avenue', 'immeuble']
        
        # Check column names
        has_property_cols = any(
            any(kw in str(col).lower() for kw in property_keywords)
            for col in df.columns
        )
        
        if has_property_cols:
            print("   ✅ Les colonnes contiennent des noms d'immeubles")
            print("   → Structure: PAR IMMEUBLE (colonnes)")
        else:
            # Check first column for property names
            first_col_values = df.iloc[:, 0].astype(str).str.lower()
            has_property_rows = any(
                any(kw in val for kw in property_keywords)
                for val in first_col_values
            )
            
            if has_property_rows:
                print("   ✅ Les lignes contiennent des noms d'immeubles")
                print("   → Structure: PAR IMMEUBLE (lignes)")
            else:
                print("   ⚠️  Pas de noms d'immeubles détectés")
                print("   → Structure: CONSOLIDÉ (global)")
        
        # Check for totals
        if 'total' in str(df.columns).lower() or any('total' in str(v).lower() for v in df.iloc[:, 0]):
            print("   ✅ Colonnes/lignes de totaux détectées")
        
        # Look for typical P&L items
        pl_items = ['revenu', 'charge', 'loyer', 'résultat', 'bénéfice', 'perte']
        pl_found = [item for item in pl_items if any(item in str(val).lower() for val in df.iloc[:, 0])]
        
        if pl_found:
            print(f"\n   📈 Postes P&L détectés: {', '.join(pl_found)}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()



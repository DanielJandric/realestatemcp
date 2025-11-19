"""
Detailed analysis of Compte de Résultat with property breakdown
"""
import pandas as pd
from pathlib import Path

print("="*80)
print("  ANALYSE DÉTAILLÉE COMPTE DE RÉSULTAT PAR IMMEUBLE")
print("="*80)

file_path = Path(r"Incremental1\00. Reporting\2024\Copie de Comptedersultat-436-BeCapitalSABaar20241211-1573736-wpg4qn.xlsx")

if file_path.exists():
    print(f"\n📄 Fichier: {file_path.name}\n")
    
    try:
        # Read Excel - header is at row 6 (0-indexed)
        df_raw = pd.read_excel(file_path, sheet_name=0)
        
        # Find header row (contains "Compte")
        header_row = None
        for idx, row in df_raw.iterrows():
            if 'Compte' in str(row.values):
                header_row = idx
                break
        
        if header_row is None:
            print("❌ Header row not found")
            exit()
        
        # Re-read with correct header
        df = pd.read_excel(file_path, sheet_name=0, header=header_row)
        
        print(f"📊 Colonnes identifiées (header à ligne {header_row}):")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        # Clean up - remove empty rows
        df = df[df['Compte'].notna() & (df['Compte'] != 'Compte')]
        
        print(f"\n📋 Données ({len(df)} lignes):\n")
        
        # Show key financial items
        key_items = []
        for idx, row in df.head(30).iterrows():
            compte = row['Compte']
            designation = row['Désignation']
            
            if pd.notna(compte) and pd.notna(designation):
                # Get values for each property
                values = {}
                for col in df.columns[3:]:  # Skip Compte, Désignation, Total
                    val = row[col]
                    if pd.notna(val):
                        try:
                            values[col] = float(val)
                        except:
                            pass
                
                if values:
                    key_items.append({
                        'compte': compte,
                        'designation': designation,
                        'values': values
                    })
        
        # Display summary
        print("🏢 IMMEUBLES DÉTECTÉS:")
        properties = [col for col in df.columns[3:] if col not in ['Total (Année courante)', '436 (Année courante)']]
        for prop in properties:
            print(f"   - {prop}")
        
        print(f"\n💰 POSTES FINANCIERS PRINCIPAUX:\n")
        
        for item in key_items[:15]:
            print(f"{item['compte']:6} - {item['designation']}")
            for prop, val in item['values'].items():
                if prop in properties:
                    print(f"         {prop:20}: {val:>15,.2f} CHF")
            print()
        
        # Calculate totals
        print(f"\n📊 RÉSUMÉ PAR IMMEUBLE:\n")
        
        # Find revenue row
        revenue_row = df[df['Désignation'].astype(str).str.contains('Recettes', case=False, na=False)].iloc[0] if len(df[df['Désignation'].astype(str).str.contains('Recettes', case=False, na=False)]) > 0 else None
        
        if revenue_row is not None:
            print("RECETTES TOTALES:")
            for prop in properties:
                if prop in revenue_row:
                    val = revenue_row[prop]
                    if pd.notna(val):
                        try:
                            print(f"   {prop:25}: {float(val):>15,.2f} CHF/an")
                        except:
                            pass
        
        # Summary statistics
        total_revenue = 0
        for prop in properties:
            if revenue_row is not None and prop in revenue_row:
                val = revenue_row[prop]
                if pd.notna(val):
                    try:
                        total_revenue += float(val)
                    except:
                        pass
        
        print(f"\n   {'TOTAL PORTEFEUILLE':25}: {total_revenue:>15,.2f} CHF/an")
        
        print(f"\n{'='*80}")
        print(f"  RECOMMANDATION")
        print(f"{'='*80}\n")
        
        print("✅ Ce fichier contient des données P&L PAR IMMEUBLE")
        print("\nDonnées disponibles:")
        print("   - Recettes locatives par propriété")
        print("   - Charges par propriété")
        print("   - Résultat net par propriété")
        print("   - Période: 01.01.2023 - 10.12.2024")
        
        print("\n💡 Import recommandé:")
        print("   1. Créer table: financial_statements")
        print("   2. Stocker P&L mensuel/annuel par propriété")
        print("   3. Permettre analyse comparative et évolution")
        
        print("\n🎯 Valeur business: HAUTE")
        print("   → Vue consolidée des performances financières")
        print("   → Comparaison entre propriétés")
        print("   → Suivi historique des résultats")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


"""
Inspect structure of sinistre and litige Excel files
"""
import pandas as pd
from pathlib import Path
import sys

# Enable UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("  INSPECTION: FICHIERS SINISTRES ET LITIGES")
print("="*80)

# Files to inspect (sample from each location)
sinistre_files = [
    r"Incremental1\Tableau suivi sinistre.xlsx",
    r"Incremental1\Centrale 3 - Martigny - DD\07. Sinistres\Tableau suivi sinistre.xlsx",
    r"Pratifori 5-7 - Sion - DD\07. Sinistres\Tableau suivi sinistre.xlsx",
]

litige_files = [
    r"Incremental1\Litiges.xlsx",
    r"Incremental1\06. Litiges\3. Litiges.xlsx",
    r"Pratifori 5-7 - Sion - DD\06. Litiges\Litiges.xlsx",
]

def inspect_file(filepath):
    print(f"\n{'='*80}")
    print(f"FILE: {filepath}")
    print(f"{'='*80}")
    
    try:
        path = Path(filepath)
        if not path.exists():
            print(f"   File not found!")
            return None
        
        # Try to read Excel file
        xl = pd.ExcelFile(path)
        print(f"\n Sheets: {xl.sheet_names}")
        
        # Read first sheet
        df = pd.read_excel(path, sheet_name=0)
        print(f"\n Rows: {len(df)}")
        print(f" Columns: {list(df.columns)}")
        
        # Show first few rows (non-empty)
        print(f"\n Sample data (first 3 non-empty rows):")
        non_empty = df.dropna(how='all').head(3)
        for idx, row in non_empty.iterrows():
            print(f"\n   Row {idx}:")
            for col in df.columns:
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    print(f"      {col}: {val}")
        
        return df
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

print("\n" + "="*80)
print("  PART 1: SINISTRES")
print("="*80)

for file in sinistre_files:
    inspect_file(file)

print("\n\n" + "="*80)
print("  PART 2: LITIGES")
print("="*80)

for file in litige_files:
    inspect_file(file)

print("\n" + "="*80)
print("  DONE")
print("="*80)



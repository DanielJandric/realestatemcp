import pandas as pd
import glob
import os

def test_extraction():
    excel_files = glob.glob("c:/OneDriveExport/*.xlsx")
    for excel_file in excel_files:
        print(f"--- Processing {os.path.basename(excel_file)} ---")
        fname = os.path.basename(excel_file)
        
        address = None
        city = None
        
        # Strategy 1: Filename parsing
        if "Etat_locatif" in fname:
            parts = fname.split("_")
            if len(parts) > 4:
                addr_parts = []
                for p in parts[3:]:
                    if p.isdigit() and len(p) == 8: # Date
                        break
                    if "au" in p and any(c.isdigit() for c in p): # Date marker
                        break
                    addr_parts.append(p)
                address = " ".join(addr_parts)
                print(f"  [Filename Strategy] Found: {address}")
        elif "Fribourg" in fname:
             address = "Rue de la Banque 4"
             city = "Fribourg"
             print(f"  [Filename Strategy] Found: {address}, {city}")

        # Strategy 2: Content parsing
        if not address:
            try:
                df_preview = pd.read_excel(excel_file, header=None, nrows=20)
                for idx, row in df_preview.iterrows():
                    row_str = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
                    if "liegenschaft" in row_str:
                        print(f"  [Content Strategy] Found keyword 'liegenschaft' in row {idx}")
                        # Try to find the address in this row
                        for cell in row.values:
                            if isinstance(cell, str) and len(cell) > 10 and "liegenschaft" not in cell.lower():
                                address = cell
                                print(f"  [Content Strategy] Extracted: {address}")
                                break
            except Exception as e:
                print(f"  Error reading file: {e}")
        
        if not address:
            print("  [Result] No address found.")
        else:
            print(f"  [Result] Final Address: {address}")

if __name__ == "__main__":
    test_extraction()

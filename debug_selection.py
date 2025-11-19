import os
from pathlib import Path
import pandas as pd

ROOT_DIR = Path("c:/OneDriveExport")

def debug_selection():
    print("Debugging file selection...")
    
    PROPERTY_DATA = {
        "Gare 28": {
            "keywords": ["Gare 28", "45634"],
            "name": "Gare 28",
            "address": "Avenue de la Gare 28",
            "city": "Sion",
            "zip_code": "1950"
        },
        "Place Centrale 3": {
            "keywords": ["Place Centrale 3", "Pl.Centrale", "45635"],
            "name": "Place Centrale 3",
            "address": "Place Centrale 3",
            "city": "Martigny",
            "zip_code": "1920"
        },
        "Gare 8-10": {
            "keywords": ["Gare 8-10", "45638"],
            "name": "Gare 8-10",
            "address": "Avenue de la Gare 8-10",
            "city": "Martigny",
            "zip_code": "1920"
        },
        "St-Hubert": {
            "keywords": ["St-Hubert", "45640"],
            "name": "St-Hubert",
            "address": "Rue Saint-Hubert 5",
            "city": "Sion",
            "zip_code": "1950"
        },
        "Grand Avenue": {
            "keywords": ["Grand Avenue", "Grand-avenue", "45641"],
            "name": "Grand Avenue",
            "address": "Grand-Avenue 6",
            "city": "Chippis",
            "zip_code": "3960"
        },
        "Pratifori 5-7": {
            "keywords": ["Pratifori", "45642"],
            "name": "Pratifori 5-7",
            "address": "Rue de Pratifori 5-7",
            "city": "Sion",
            "zip_code": "1950"
        },
        "Banque 4": {
            "keywords": ["Banque 4", "2805", "Fribourg"],
            "name": "Banque 4",
            "address": "Rue de la Banque 4",
            "city": "Fribourg",
            "zip_code": "1700"
        },
        "Pre d'Emoz": {
            "keywords": ["Pre d_Emoz", "2133"],
            "name": "Pre d'Emoz",
            "address": "Chemin du Pré d'Emoz 41-45",
            "city": "Aigle",
            "zip_code": "1860"
        }
    }
    
    all_xlsx = list(ROOT_DIR.rglob("*.xlsx"))
    print(f"Total Excel files found: {len(all_xlsx)}")
    
    excel_files = []
    
    for prop_key, data in PROPERTY_DATA.items():
        keywords = data["keywords"]
        candidates = []
        for f in all_xlsx:
            fname = f.name
            fpath = str(f)
            if "~$" in fname or "Rapports CBRE" in fpath or "Litiges" in fpath or "Sinistres" in fpath: continue
            is_rent_roll = any(x in fname.lower() for x in ["etat", "mieter", "el ", "el_"])
            if not is_rent_roll: continue
            if any(k.lower() in fname.lower() for k in keywords):
                candidates.append(f)
        
        print(f"Property: {prop_key}, Candidates: {len(candidates)}")
        if candidates:
             # Sort by heuristic score
            best_cand = None
            best_score = -1
            for cand in candidates:
                score = 0
                if "Actualisés" in str(cand): score += 100
                if "31.10.2025" in cand.name: score += 50
                if "2025" in cand.name: score += 20
                if "2024" in cand.name: score += 10
                if score > best_score:
                    best_score = score
                    best_cand = cand
                elif score == best_score:
                    if len(str(cand)) < len(str(best_cand)): best_cand = cand
            
            if best_cand:
                print(f"  SELECTED: {best_cand.name}")
                excel_files.append(best_cand)
        else:
            print(f"  WARNING: No file found")

    print(f"Final list size: {len(excel_files)}")

if __name__ == "__main__":
    debug_selection()

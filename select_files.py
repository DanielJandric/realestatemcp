import os
import glob
import re
from pathlib import Path

ROOT_DIR = Path("c:/OneDriveExport")

# Known property keywords/IDs
PROPERTIES = {
    "Gare 28": ["Gare 28", "45634"],
    "Place Centrale 3": ["Place Centrale 3", "Pl.Centrale", "45635"],
    "Gare 8-10": ["Gare 8-10", "45638"],
    "St-Hubert": ["St-Hubert", "45640"],
    "Grand Avenue": ["Grand Avenue", "Grand-avenue", "45641"],
    "Pratifori 5-7": ["Pratifori", "45642"],
    "Banque 4": ["Banque 4", "2805", "Fribourg"],
    "Pre d'Emoz": ["Pre d_Emoz", "2133"]
}

def get_date_from_filename(fname):
    # Try to find YYYYMMDD or DD.MM.YYYY
    # 20250402
    match = re.search(r"(\d{4})(\d{2})(\d{2})", fname)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    # 31.10.2025
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", fname)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    
    return "0000-00-00"

def main():
    all_xlsx = list(ROOT_DIR.rglob("*.xlsx"))
    selected_files = {}

    for prop_name, keywords in PROPERTIES.items():
        candidates = []
        for f in all_xlsx:
            fname = f.name
            fpath = str(f)
            
            # Skip temp files or irrelevant folders
            if "~$" in fname or "Rapports CBRE" in fpath or "Litiges" in fpath or "Sinistres" in fpath:
                continue
            
            # Check if file matches property keywords
            # Must match at least one keyword strongly
            # And look like a rent roll (Etat locatif, Mieterspiegel, EL)
            is_rent_roll = any(x in fname.lower() for x in ["etat", "mieter", "el ", "el_"])
            if not is_rent_roll:
                continue

            if any(k.lower() in fname.lower() for k in keywords):
                candidates.append(f)
        
        if not candidates:
            print(f"WARNING: No file found for {prop_name}")
            continue
            
        # Sort by date in filename, then modification time
        # Simple heuristic: prefer "Actualisés" folder
        best_cand = None
        best_score = -1
        
        for cand in candidates:
            score = 0
            if "Actualisés" in str(cand): score += 100
            if "31.10.2025" in cand.name: score += 50 # Future/Recent date
            if "2025" in cand.name: score += 20
            if "2024" in cand.name: score += 10
            
            if score > best_score:
                best_score = score
                best_cand = cand
            elif score == best_score:
                # Tie break by length (shorter might be cleaner?) or modification time
                if len(str(cand)) < len(str(best_cand)):
                    best_cand = cand
        
        selected_files[prop_name] = best_cand
        print(f"Selected for {prop_name}: {best_cand.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    main()

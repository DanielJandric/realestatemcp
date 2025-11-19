import pandas as pd
import os
import uuid
import requests
import json
from pathlib import Path
import datetime
import time
import unicodedata

# Configuration
ROOT_DIR = Path("c:/OneDriveExport")
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def generate_uuid():
    return str(uuid.uuid4())

def parse_date(date_val):
    if pd.isna(date_val) or date_val == "":
        return None
    try:
        if isinstance(date_val, str):
            for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    return datetime.datetime.strptime(date_val, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None
        return date_val.strftime("%Y-%m-%d")
    except:
        return None

def normalize_text(value: str) -> str:
    """
    Normalize column names for loose matching (lowercase, ASCII, no punctuation).
    """
    normalized = unicodedata.normalize("NFKD", value.replace("’", "'"))
    ascii_text = normalized.encode("ascii", "ignore").decode()
    return ascii_text.lower().strip()

def parse_money(val):
    if pd.isna(val) or val == "":
        return 0
    if isinstance(val, str):
        try:
            return float(val.replace("'", "").replace("CHF", "").strip())
        except:
            return 0
    return float(val)

def upsert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        response = requests.post(url, headers=HEADERS, json=data)
        if response.status_code not in [200, 201]:
            print(f"Error upserting to {table}: {response.status_code} - {response.text}")
        return response
    except Exception as e:
        print(f"Exception upserting to {table}: {e}")

def main():
    print("Starting Supabase Sync...")
    
    # 0. Fetch existing properties to avoid duplicates
    print("Fetching existing properties...")
    properties_map = {}
    try:
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/properties?select=id,name", headers=HEADERS)
        if resp.status_code == 200:
            for p in resp.json():
                properties_map[p["name"]] = p["id"]
    except Exception as e:
        print(f"Error fetching properties: {e}")

    # 1. Find Excel Files (Targeted Selection)
    print("Selecting best Excel files for properties...")
    # Golden Records for Properties
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
    excel_files = []
    property_metadata = {} # filename -> {name, address, city, zip}
    
    print(f"DEBUG: Found {len(all_xlsx)} total Excel files in workspace.")

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
                print(f"Selected for {prop_key}: {best_cand.name}")
                excel_files.append(best_cand)
                property_metadata[best_cand.name] = data
        else:
            print(f"WARNING: No file found for {prop_key}")

    print(f"Found {len(excel_files)} unique property files.")

    # properties_map = {} # name -> uuid (Already populated)
    tenants_map = {} # name -> uuid
    units_map = {} # unit_key -> uuid

    # We will collect data in lists and batch insert/upsert if possible, or just one by one for safety
    # Supabase supports batch inserts
    
    properties_batch = []
    tenants_batch = []
    units_batch = []
    leases_batch = []
    documents_batch = []

    for excel_file in excel_files:
        print(f"Processing {excel_file.name}...")
        
        # Use Golden Record Data
        meta = property_metadata.get(excel_file.name)
        prop_name = meta["name"]
        
        if prop_name not in properties_map:
            prop_id = generate_uuid()
            properties_map[prop_name] = prop_id
        else:
            prop_id = properties_map[prop_name]

        # Ensure property is in batch for update with correct details
        # Remove if exists with old data (simplified: just append, upsert handles it)
        # Better: Check if ID is in batch, if so update it. If not, append.
        
        found = False
        for p in properties_batch:
            if p["id"] == prop_id:
                p["name"] = prop_name
                p["address"] = meta["address"]
                p["city"] = meta["city"]
                p["zip_code"] = meta["zip_code"]
                found = True
                break
        
        if not found:
            properties_batch.append({
                "id": prop_id,
                "name": prop_name,
                "address": meta["address"],
                "city": meta["city"],
                "zip_code": meta["zip_code"]
            })

        try:
            df_preview = pd.read_excel(excel_file, header=None, nrows=20)
            
            # Restore Header Detection
            header_row_idx = 0
            for idx, row in df_preview.iterrows():
                row_str = " ".join([str(x) for x in row.values]).lower()
                if "mieter" in row_str or "locataire" in row_str or "objekt" in row_str:
                    header_row_idx = idx
                    break
            
            print(f"  Header found at row {header_row_idx}")

            df = pd.read_excel(excel_file, header=header_row_idx)
            df.columns = [str(c).strip() for c in df.columns]
            
            col_map = {}
            col_priority = {}

            def register_col(key: str, col_name: str, priority: int):
                current_priority = col_priority.get(key, -1)
                if priority > current_priority:
                    col_map[key] = col_name
                    col_priority[key] = priority

            for col in df.columns:
                l_col_raw = col.lower()
                l_col = normalize_text(col)

                # Unit / object reference detection
                if "reference" in l_col and ("objet" in l_col or "object" in l_col):
                    register_col("unit", col, 3)
                elif any(token in l_col for token in ["numero objet", "no objet", "num objet"]):
                    register_col("unit", col, 2)
                elif "objet" in l_col or "objekt" in l_col:
                    register_col("unit", col, 1)

                # Tenant name detection
                if ("nom" in l_col and "locataire" in l_col) or "name tenant" in l_col:
                    register_col("tenant", col, 3)
                elif "locataire" in l_col or "tenant" in l_col or "mieter" in l_col:
                    register_col("tenant", col, 2)
                elif "nom" in l_col and "contrat" not in l_col:
                    register_col("tenant", col, 1)

                # Rooms
                if "pieces" in l_col or "zimmer" in l_col or "rooms" in l_col:
                    register_col("rooms", col, 2)

                # Area / surface
                if "surface" in l_col or "fla" in l_col or l_col.endswith(" m2") or l_col == "m2":
                    register_col("area", col, 2)

                # Rent
                if ("loyer net" in l_col and "m2" not in l_col) or "nettomiete" in l_col:
                    register_col("rent", col, 3)
                elif "loyer net" in l_col:
                    register_col("rent", col, 2)
                elif "loyer" in l_col or "rent" in l_col:
                    register_col("rent", col, 1)

                # Charges
                if ("charges" in l_col and ("forfait" in l_col or "acompte" in l_col)) or "akonto" in l_col:
                    register_col("charges", col, 2)
                elif "charges" in l_col:
                    register_col("charges", col, 1)

                # Start / end dates
                if "debut" in l_col or "mietbeginn" in l_col or "start" in l_col:
                    register_col("start", col, 2)
                if "fin" in l_col or "mietende" in l_col or "end" in l_col:
                    register_col("end", col, 2)

                # Floor
                if "etage" in l_col or "stockwerk" in l_col or "floor" in l_col:
                    register_col("floor", col, 2)

            for _, row in df.iterrows():
                tenant_name = row.get(col_map.get("tenant"))
                if pd.isna(tenant_name) or str(tenant_name).strip() == "":
                    continue
                
                tenant_name = str(tenant_name).strip()
                
                lower_name = tenant_name.lower()
                if any(x in lower_name for x in ["ansprechpartner", "stichtag", "eigentümer", "gesamttotal", "total", "objekt", "mieter"]):
                    continue
                
                if tenant_name.replace(".", "").isdigit() or (len(tenant_name) > 5 and tenant_name[0].isdigit() and "." in tenant_name):
                     continue

                if tenant_name not in tenants_map:
                    tenant_id = generate_uuid()
                    tenants_map[tenant_name] = tenant_id
                    tenants_batch.append({
                        "id": tenant_id,
                        "name": tenant_name
                    })
                else:
                    tenant_id = tenants_map[tenant_name]

                unit_ref = str(row.get(col_map.get("unit"), "Unknown"))
                unit_key = f"{prop_name}_{unit_ref}"
                
                if unit_key not in units_map:
                    unit_id = generate_uuid()
                    units_map[unit_key] = unit_id
                    
                    u_type = 'Appartement'
                    if 'park' in unit_ref.lower() or 'garage' in unit_ref.lower():
                        u_type = 'Parking'
                    elif 'gewerbe' in unit_ref.lower() or 'comm' in unit_ref.lower():
                        u_type = 'Commercial'

                    units_batch.append({
                        "id": unit_id,
                        "property_id": prop_id,
                        "unit_number": unit_ref,
                        "floor": str(row.get(col_map.get("floor"))) if pd.notna(row.get(col_map.get("floor"))) else None,
                        "type": u_type,
                        "surface_area": parse_money(row.get(col_map.get("area"))),
                        "rooms": parse_money(row.get(col_map.get("rooms")))
                    })
                else:
                    unit_id = units_map[unit_key]

                lease_id = generate_uuid()
                leases_batch.append({
                    "id": lease_id,
                    "unit_id": unit_id,
                    "tenant_id": tenant_id,
                    "start_date": parse_date(row.get(col_map.get("start"))),
                    "end_date": parse_date(row.get(col_map.get("end"))),
                    "rent_net": parse_money(row.get(col_map.get("rent"))),
                    "charges": parse_money(row.get(col_map.get("charges")))
                })

        except Exception as e:
            print(f"Error processing {excel_file.name}: {e}")

    # Scan Documents
    print("Scanning directories for documents...")
    subdirs = [d for d in ROOT_DIR.iterdir() if d.is_dir()]
    
    for subdir in subdirs:
        dirname = subdir.name
        matched_tenant_id = None
        
        # print(f"Checking dir: {dirname}") 
        
        for t_name, t_id in tenants_map.items():
            # Try matching full last name or first part
            t_parts = t_name.lower().replace(",", "").split(" ")
            t_first = t_parts[0]
            
            d_clean = dirname.lower()
            
            # Match if the first significant part of tenant name is in directory name
            if len(t_first) > 3 and t_first in d_clean:
                # print(f"  Matched {t_name} to {dirname}")
                matched_tenant_id = t_id
                break
            
            # Also try second part if exists (sometimes first part is 'M.' or similar, though we filtered those)
            if len(t_parts) > 1:
                t_second = t_parts[1]
                if len(t_second) > 3 and t_second in d_clean:
                     # print(f"  Matched {t_name} to {dirname} (via {t_second})")
                     matched_tenant_id = t_id
                     break
        
        if matched_tenant_id:
            for file_path in subdir.glob("**/*"):
                if file_path.is_file():
                    doc_id = generate_uuid()
                    documents_batch.append({
                        "id": doc_id,
                        "tenant_id": matched_tenant_id,
                        "file_path": str(file_path.relative_to(ROOT_DIR)),
                        "file_name": file_path.name,
                        "file_type": file_path.suffix.lower()
                    })

    # Sync to Supabase
    print(f"Syncing {len(properties_batch)} properties...")
    print(json.dumps(properties_batch, indent=2)) # Debug
    if properties_batch: upsert("properties", properties_batch)
    
    print(f"Syncing {len(tenants_batch)} tenants...")
    if tenants_batch: upsert("tenants", tenants_batch)
    
    print(f"Syncing {len(units_batch)} units...")
    if units_batch: upsert("units", units_batch)
    
    print(f"Syncing {len(leases_batch)} leases...")
    if leases_batch: upsert("leases", leases_batch)
    
    print(f"Syncing {len(documents_batch)} documents...")
    if documents_batch: upsert("documents", documents_batch)

    print("Sync complete!")

if __name__ == "__main__":
    main()

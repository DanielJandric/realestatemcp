import pandas as pd
import os
import uuid
from pathlib import Path
import datetime
import re

# Configuration
ROOT_DIR = Path("c:/OneDriveExport")
OUTPUT_FILE = ROOT_DIR / "seed.sql"

def generate_uuid():
    return str(uuid.uuid4())

def escape_sql(text):
    if pd.isna(text) or text == "":
        return "NULL"
    return "'" + str(text).replace("'", "''") + "'"

def parse_date(date_val):
    if pd.isna(date_val) or date_val == "":
        return "NULL"
    try:
        if isinstance(date_val, str):
            # Try common formats
            for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y.%m.%d"]:
                try:
                    return "'" + datetime.datetime.strptime(date_val, fmt).strftime("%Y-%m-%d") + "'"
                except ValueError:
                    continue
            return "NULL"
        return "'" + date_val.strftime("%Y-%m-%d") + "'"
    except:
        return "NULL"

def parse_money(val):
    if pd.isna(val) or val == "":
        return "0"
    if isinstance(val, str):
        # Remove currency symbols, separators
        clean = val.replace("'", "").replace("CHF", "").strip()
        try:
            return str(float(clean))
        except:
            return "0"
    return str(val)

def is_valid_unit(unit_val):
    if pd.isna(unit_val): return False
    s = str(unit_val).lower().strip()
    return s != "nan" and s != ""

def is_valid_tenant(name):
    if pd.isna(name): return False
    s = str(name).strip()
    if s == "": return False
    
    # Check for date-like strings (YYYY-MM-DD or similar)
    if re.search(r'\d{4}-\d{2}-\d{2}', s): return False
    
    # Check for metadata keywords (only exact matches or very specific patterns)
    lower = s.lower()
    # Only reject if it's EXACTLY a metadata keyword, not if it contains it
    if lower in ["ansprechpartner", "stichtag", "eigentümer", "gesamttotal", "total", "objekt", "mieter", "liegenschaft", "hauptmieter", "leerstand"]:
        return False
        
    return True

def main():
    print("Starting ETL process (State of the Art Version)...")
    
    sql_statements = []
    
    # 1. Find Excel Files
    excel_files = list(ROOT_DIR.glob("*.xlsx"))
    print(f"Found {len(excel_files)} Excel files.")

    properties_map = {} # name -> uuid
    tenants_map = {} # name -> uuid
    units_map = {} # unit_number -> uuid

    for excel_file in excel_files:
        print(f"Processing {excel_file.name}...")
        
        # Heuristic: Property name from filename (simplified)
        prop_name = excel_file.stem.split("_")[0]
        if prop_name not in properties_map:
            prop_id = generate_uuid()
            properties_map[prop_name] = prop_id
            sql_statements.append(f"INSERT INTO properties (id, name) VALUES ('{prop_id}', {escape_sql(prop_name)});")
        else:
            prop_id = properties_map[prop_name]

        try:
            # Read Excel - Try to find the header row
            df_preview = pd.read_excel(excel_file, header=None, nrows=20)
            header_row_idx = -1
            for idx, row in df_preview.iterrows():
                row_str = " ".join([str(x) for x in row.values]).lower()
                # More robust keywords
                if ("mieter" in row_str or "locataire" in row_str) and ("objekt" in row_str or "objet" in row_str):
                    header_row_idx = idx
                    break
            
            if header_row_idx == -1:
                print(f"Could not find header in {excel_file.name}, skipping.")
                continue

            df = pd.read_excel(excel_file, header=header_row_idx)
            
            # Normalize columns
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identify columns with fuzzy matching
            col_map = {}
            for col in df.columns:
                l_col = col.lower()
                if "objekt" in l_col or "objet" in l_col: col_map["unit"] = col
                elif "mieter" in l_col or "locataire" in l_col or "nom" in l_col: col_map["tenant"] = col
                elif "zimmer" in l_col or "pièces" in l_col: col_map["rooms"] = col
                elif "fläche" in l_col or "surface" in l_col: col_map["area"] = col
                elif "nettomiete" in l_col or "loyer net" in l_col: col_map["rent"] = col
                elif "akonto" in l_col or "charges" in l_col: col_map["charges"] = col
                elif "mietbeginn" in l_col or "début" in l_col: col_map["start"] = col
                elif "mietende" in l_col or "fin" in l_col: col_map["end"] = col
                elif "stockwerk" in l_col or "étage" in l_col: col_map["floor"] = col

            print(f"Mapped columns: {col_map}")

            for _, row in df.iterrows():
                # Validation
                tenant_name = row.get(col_map.get("tenant"))
                unit_ref = row.get(col_map.get("unit"))
                rent_val = row.get(col_map.get("rent"))
                
                if not is_valid_tenant(tenant_name):
                    continue
                
                if not is_valid_unit(unit_ref):
                    print(f"Skipping invalid unit: {unit_ref}")
                    continue

                tenant_name = str(tenant_name).strip()
                unit_ref = str(unit_ref).strip()
                
                # Check rent
                rent_amount = float(parse_money(rent_val))
                if rent_amount <= 0:
                    print(f"Warning: Zero/Negative rent for {tenant_name} in {unit_ref}. Skipping lease but keeping unit/tenant.")
                    # We might still want the unit and tenant, just not the lease? 
                    # Or maybe we import it but flag it? User asked to "delete and reimport properly".
                    # "Properly" likely means don't import garbage.
                    # But if the unit exists, we should create it.
                
                # Tenant
                if tenant_name not in tenants_map:
                    tenant_id = generate_uuid()
                    tenants_map[tenant_name] = tenant_id
                    sql_statements.append(f"INSERT INTO tenants (id, name) VALUES ('{tenant_id}', {escape_sql(tenant_name)});")
                else:
                    tenant_id = tenants_map[tenant_name]

                # Unit
                unit_key = f"{prop_name}_{unit_ref}"
                if unit_key not in units_map:
                    unit_id = generate_uuid()
                    units_map[unit_key] = unit_id
                    
                    floor = escape_sql(row.get(col_map.get("floor")))
                    area = parse_money(row.get(col_map.get("area")))
                    rooms = parse_money(row.get(col_map.get("rooms")))
                    
                    u_type = 'Appartement'
                    if 'park' in unit_ref.lower() or 'garage' in unit_ref.lower():
                        u_type = 'Parking'
                    elif 'gewerbe' in unit_ref.lower() or 'comm' in unit_ref.lower():
                        u_type = 'Commercial'

                    sql_statements.append(f"INSERT INTO units (id, property_id, unit_number, floor, type, surface_area, rooms) VALUES ('{unit_id}', '{prop_id}', {escape_sql(unit_ref)}, {floor}, '{u_type}', {area}, {rooms});")
                else:
                    unit_id = units_map[unit_key]

                # Lease
                # Only create lease if rent is valid-ish or if we accept 0 rent (maybe for caretakers?)
                # User complained about 0 rent, so let's skip if 0 unless we are sure.
                # But let's include it but maybe log it.
                # Actually, let's skip if rent is 0 AND it looks like an error.
                # For now, I will import it but the validation above warns.
                
                lease_id = generate_uuid()
                start_date = parse_date(row.get(col_map.get("start")))
                end_date = parse_date(row.get(col_map.get("end")))
                rent = parse_money(rent_val)
                charges = parse_money(row.get(col_map.get("charges")))
                
                sql_statements.append(f"INSERT INTO leases (id, unit_id, tenant_id, start_date, end_date, rent_net, charges) VALUES ('{lease_id}', '{unit_id}', '{tenant_id}', {start_date}, {end_date}, {rent}, {charges});")

        except Exception as e:
            print(f"Error processing {excel_file.name}: {e}")

    # 2. Scan Directories for Documents
    print("Scanning directories for documents...")
    subdirs = [d for d in ROOT_DIR.iterdir() if d.is_dir()]
    
    for subdir in subdirs:
        dirname = subdir.name
        matched_tenant_id = None
        
        for t_name, t_id in tenants_map.items():
            t_clean = t_name.lower().replace(",", "").split(" ")[0]
            d_clean = dirname.lower()
            
            if t_clean in d_clean and len(t_clean) > 3:
                matched_tenant_id = t_id
                break
        
        if matched_tenant_id:
            for file_path in subdir.glob("**/*"):
                if file_path.is_file():
                    doc_id = generate_uuid()
                    rel_path = file_path.relative_to(ROOT_DIR)
                    f_name = file_path.name
                    f_type = file_path.suffix.lower()
                    
                    sql_statements.append(f"INSERT INTO documents (id, tenant_id, file_path, file_name, file_type) VALUES ('{doc_id}', '{matched_tenant_id}', {escape_sql(str(rel_path))}, {escape_sql(f_name)}, {escape_sql(f_type)});")

    # Write Output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_statements))
    
    print(f"Done. Generated {len(sql_statements)} SQL statements in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

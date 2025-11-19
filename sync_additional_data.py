import pandas as pd
import os
import uuid
import requests
import json
import datetime
from pathlib import Path

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
    print("Starting Additional Data Sync...")
    
    # Fetch existing properties/tenants for linking
    print("Fetching existing properties and tenants...")
    properties_map = {} # name -> uuid
    tenants_map = {} # name -> uuid
    
    try:
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/properties?select=id,name", headers=HEADERS)
        if resp.status_code == 200:
            for p in resp.json():
                properties_map[p["name"]] = p["id"]
                
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/tenants?select=id,name", headers=HEADERS)
        if resp.status_code == 200:
            for t in resp.json():
                tenants_map[t["name"]] = t["id"]
    except Exception as e:
        print(f"Error fetching refs: {e}")
        return

    # 1. Litiges (Disputes)
    print("Processing Litiges...")
    litiges_file = ROOT_DIR / "Incremental1/Litiges.xlsx"
    disputes_batch = []
    if litiges_file.exists():
        try:
            df = pd.read_excel(litiges_file, header=2) # Row 2 is header
            # Columns: No, Immeuble, Locataire, Description, Montant, Statut, Date
            
            for _, row in df.iterrows():
                # Try to link property
                prop_id = None
                prop_ref = str(row.get("Immeuble", ""))
                # Heuristic match
                for pname, pid in properties_map.items():
                    if pname in prop_ref or prop_ref in pname:
                        prop_id = pid
                        break
                
                # Try to link tenant
                tenant_id = None
                tenant_ref = str(row.get("Locataire", ""))
                for tname, tid in tenants_map.items():
                    if tname in tenant_ref:
                        tenant_id = tid
                        break
                
                disputes_batch.append({
                    "property_id": prop_id,
                    "tenant_id": tenant_id,
                    "description": str(row.get("Description", "")),
                    "status": str(row.get("Statut", "")),
                    "amount": parse_money(row.get("Montant")),
                    "date": parse_date(row.get("Date"))
                })
        except Exception as e:
            print(f"Error processing Litiges: {e}")

    if disputes_batch:
        print(f"Syncing {len(disputes_batch)} disputes...")
        upsert("disputes", disputes_batch)

    # 2. Sinistres (Incidents)
    print("Processing Sinistres...")
    sinistres_file = ROOT_DIR / "Incremental1/Tableau suivi sinistre.xlsx"
    incidents_batch = []
    if sinistres_file.exists():
        try:
            df = pd.read_excel(sinistres_file, header=2) # Row 2 is header
            # Columns: No, Immeuble, Locataire, Description, Date, Ref Assurance, Statut
            
            for _, row in df.iterrows():
                prop_id = None
                prop_ref = str(row.get("Immeuble", ""))
                for pname, pid in properties_map.items():
                    if pname in prop_ref or prop_ref in pname:
                        prop_id = pid
                        break
                
                tenant_id = None
                tenant_ref = str(row.get("Locataire", ""))
                for tname, tid in tenants_map.items():
                    if tname in tenant_ref:
                        tenant_id = tid
                        break
                
                incidents_batch.append({
                    "property_id": prop_id,
                    "tenant_id": tenant_id,
                    "description": str(row.get("Description", "")),
                    "status": str(row.get("Statut", "")),
                    "date": parse_date(row.get("Date")),
                    "insurance_ref": str(row.get("Ref Assurance", ""))
                })
        except Exception as e:
            print(f"Error processing Sinistres: {e}")

    if incidents_batch:
        print(f"Syncing {len(incidents_batch)} incidents...")
        upsert("incidents", incidents_batch)

    # 3. Maintenance
    print("Processing Maintenance...")
    maint_file = ROOT_DIR / "Incremental1/09. Contrats de maintenance/Becapital_contrats d'entretien_Gare 28 Sion_Màj au 05.09.2024.xlsx"
    maintenance_batch = []
    if maint_file.exists():
        try:
            df = pd.read_excel(maint_file, header=0) # Row 0 seems to be header based on preview
            # Columns: Immeuble, Fournisseur, Description, Début, Fin, Coût
            
            for _, row in df.iterrows():
                prop_id = None
                prop_ref = str(row.get("Immeuble", ""))
                for pname, pid in properties_map.items():
                    if pname in prop_ref or prop_ref in pname:
                        prop_id = pid
                        break
                
                maintenance_batch.append({
                    "property_id": prop_id,
                    "provider": str(row.get("Fournisseur", "")),
                    "description": str(row.get("Description", "")),
                    "start_date": parse_date(row.get("Début")),
                    "end_date": parse_date(row.get("Fin")),
                    "cost": parse_money(row.get("Coût"))
                })
        except Exception as e:
            print(f"Error processing Maintenance: {e}")

    if maintenance_batch:
        print(f"Syncing {len(maintenance_batch)} maintenance contracts...")
        upsert("maintenance", maintenance_batch)

    print("Additional Data Sync Complete!")

if __name__ == "__main__":
    main()

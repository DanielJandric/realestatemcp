from supabase import create_client, Client
import re

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_corruption():
    with open("corruption_report.txt", "w", encoding="utf-8") as f:
        f.write("Scanning for data corruption...\n")
        
        # 1. Check for 'nan' unit numbers
        f.write("\n--- Checking for 'nan' unit numbers ---\n")
        units = supabase.table("units").select("*, properties(name)").eq("unit_number", "nan").execute()
        if units.data:
            f.write(f"Found {len(units.data)} units with 'nan' number.\n")
            affected_props = set(u['properties']['name'] for u in units.data if u['properties'])
            f.write(f"Affected properties: {affected_props}\n")
        else:
            f.write("No 'nan' units found.\n")

        # 2. Check for date-like tenant names
        f.write("\n--- Checking for date-like tenant names ---\n")
        tenants = supabase.table("tenants").select("*").execute()
        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
        suspicious_tenants = []
        for t in tenants.data:
            if date_pattern.search(t['name']):
                suspicious_tenants.append(t)
                
        if suspicious_tenants:
            f.write(f"Found {len(suspicious_tenants)} tenants with date-like names.\n")
            f.write(f"Examples: {[t['name'] for t in suspicious_tenants[:5]]}\n")
        else:
            f.write("No suspicious tenant names found.\n")

        # 3. Check for suspicious rents
        f.write("\n--- Checking for suspicious rents (< 200 or 0) ---\n")
        leases = supabase.table("leases").select("*, units(properties(name))").lt("rent_net", 200).execute()
        if leases.data:
            f.write(f"Found {len(leases.data)} leases with rent < 200.\n")
            for l in leases.data:
                 prop_name = l['units']['properties']['name'] if l['units'] and l['units']['properties'] else "Unknown"
                 f.write(f"  - Rent: {l['rent_net']}, Property: {prop_name}\n")
        else:
            f.write("No suspicious rents found.\n")

if __name__ == "__main__":
    check_corruption()

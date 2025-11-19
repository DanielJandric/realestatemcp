from supabase import create_client, Client
import re

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_fresh_data():
    with open("fresh_data_verification.txt", "w", encoding="utf-8") as f:
        f.write("=== Verifying Fresh Data Quality ===\n\n")
        
        # Get summary stats
        f.write("--- Database Summary ---\n")
        props = supabase.table("properties").select("*", count="exact").execute()
        tenants = supabase.table("tenants").select("*", count="exact").execute()
        units = supabase.table("units").select("*", count="exact").execute()
        leases = supabase.table("leases").select("*", count="exact").execute()
        
        f.write(f"Properties: {props.count}\n")
        f.write(f"Tenants: {tenants.count}\n")
        f.write(f"Units: {units.count}\n")
        f.write(f"Leases: {leases.count}\n")
        
        # Check for 'nan' unit numbers
        f.write("\n--- Checking for 'nan' unit numbers ---\n")
        nan_units = supabase.table("units").select("*, properties(name)").eq("unit_number", "nan").execute()
        if nan_units.data:
            f.write(f"⚠️ Found {len(nan_units.data)} units with 'nan' number!\n")
            for u in nan_units.data:
                f.write(f"  - Property: {u['properties']['name']}, Unit: {u['unit_number']}\n")
        else:
            f.write("✅ No 'nan' units found\n")
        
        # Check for date-like tenant names
        f.write("\n--- Checking for date-like tenant names ---\n")
        all_tenants = supabase.table("tenants").select("*").execute()
        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
        date_tenants = [t for t in all_tenants.data if date_pattern.search(t['name'])]
        
        if date_tenants:
            f.write(f"⚠️ Found {len(date_tenants)} tenants with date-like names!\n")
            for t in date_tenants[:10]:
                f.write(f"  - {t['name']}\n")
        else:
            f.write("✅ No date-like tenant names found\n")
        
        # Check rent distribution
        f.write("\n--- Rent Distribution Analysis ---\n")
        all_leases = supabase.table("leases").select("rent_net").execute()
        rents = [l['rent_net'] for l in all_leases.data if l['rent_net'] is not None]
        
        zero_rents = len([r for r in rents if r == 0])
        low_rents = len([r for r in rents if 0 < r < 100])
        mid_rents = len([r for r in rents if 100 <= r < 500])
        high_rents = len([r for r in rents if r >= 500])
        
        f.write(f"Zero rent: {zero_rents}\n")
        f.write(f"Low rent (1-99 CHF): {low_rents} - likely parking/storage\n")
        f.write(f"Mid rent (100-499 CHF): {mid_rents}\n")
        f.write(f"High rent (500+ CHF): {high_rents}\n")
        
        if zero_rents > 0:
            f.write(f"\n⚠️ {zero_rents} leases with zero rent - may need investigation\n")
        
        # Sample some data
        f.write("\n--- Sample Properties ---\n")
        for p in props.data:
            f.write(f"  - {p['name']} ({p.get('city', 'N/A')})\n")
        
        f.write("\n--- Sample Tenants ---\n")
        for t in tenants.data[:10]:
            f.write(f"  - {t['name']}\n")
        
        f.write("\n✅ Verification complete!\n")
    
    print("Verification saved to fresh_data_verification.txt")

if __name__ == "__main__":
    verify_fresh_data()

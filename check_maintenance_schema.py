"""
Check maintenance table schema
"""
from supabase import create_client

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  SCHEMA TABLE MAINTENANCE")
print("="*80)

# Try to get schema
try:
    result = supabase.table("maintenance").select("*").limit(1).execute()
    
    if result.data:
        print("\nCHAMPS EXISTANTS:")
        for key in sorted(result.data[0].keys()):
            value = result.data[0][key]
            value_type = type(value).__name__
            print(f"   {key:25} : {value_type:15} = {value}")
    else:
        print("\nTable vide, tentative de voir les colonnes via une insertion vide...")
        
except Exception as e:
    print(f"\n❌ Erreur: {str(e)}")
    print("\nLa table 'maintenance' n'existe peut-être pas encore.")
    print("Colonnes attendues selon schema_improvements.sql:")
    print("""
   - id                    UUID          PRIMARY KEY
   - property_id           UUID          REFERENCES properties
   - unit_id               UUID          REFERENCES units (OPTIONAL)
   - contract_type         TEXT          (ex: 'chauffage', 'ascenseur', etc.)
   - vendor_name           TEXT          Nom du prestataire
   - description           TEXT          Description du contrat
   - start_date            DATE          Date début
   - end_date              DATE          Date fin
   - annual_cost           NUMERIC       Coût annuel
   - frequency             TEXT          Fréquence (mensuel, trimestriel, annuel)
   - status                TEXT          (actif, expiré, résilié)
   - created_at            TIMESTAMP
    """)



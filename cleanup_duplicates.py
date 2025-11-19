import requests
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

VALID_NAMES = [
    "Gare 28",
    "Place Centrale 3",
    "Gare 8-10",
    "St-Hubert",
    "Grand Avenue",
    "Pratifori 5-7",
    "Banque 4",
    "Pre d'Emoz"
]

def cleanup():
    print("Fetching properties...")
    url = f"{SUPABASE_URL}/rest/v1/properties?select=id,name"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()
    
    for p in data:
        if p["name"] not in VALID_NAMES:
            print(f"Deleting invalid property: {p['name']} ({p['id']})")
            del_url = f"{SUPABASE_URL}/rest/v1/properties?id=eq.{p['id']}"
            requests.delete(del_url, headers=HEADERS)
        else:
            print(f"Keeping valid property: {p['name']}")

if __name__ == "__main__":
    cleanup()

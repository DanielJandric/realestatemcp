import requests
import json

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def count(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=count"
    resp = requests.get(url, headers=HEADERS)
    # Range header for count? Or just select=count
    # Supabase returns count in Content-Range header usually if we ask for it, or we can just get all and len() for small data
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=id"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()
    print(f"{table}: {len(data)}")

count("properties")
count("tenants")
count("units")
count("leases")
count("documents")

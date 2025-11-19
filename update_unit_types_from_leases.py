"""
Update the 'type' column in units table based on extracted lease documents
Uses the lease document filenames and content to infer unit types
"""
from supabase import create_client
import re
from dotenv import load_dotenv
import os

load_dotenv()

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

AZURE_ENDPOINT = os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT", "")
AZURE_KEY = os.environ.get("AZURE_FORM_RECOGNIZER_KEY", "")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  MISE À JOUR DES TYPES D'UNITÉS")
print("="*80)

# Check current types
print("\n📊 État actuel de la colonne 'type':")
units = supabase.table("units").select("type").execute().data
type_counts = {}
for unit in units:
    t = unit.get('type') or 'None'
    type_counts[t] = type_counts.get(t, 0) + 1

for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {t:20}: {count}")

# Get all lease documents
docs = supabase.table("documents").select("*").filter("category", "eq", "lease").execute().data
print(f"\n📄 {len(docs)} baux disponibles pour l'analyse")

# Function to detect type from filename
def detect_type_from_filename(filename):
    """Detect unit type from lease filename"""
    filename_lower = filename.lower()
    
    # Parking (most specific first)
    if re.search(r'\bpp\b|parking|place.*parc|garage', filename_lower):
        return 'parking'
    # Bureau
    elif re.search(r'\bbureau\b|office|cabinet', filename_lower):
        return 'bureau'
    # Commerce
    elif re.search(r'commerce|commercial|magasin|boutique|arcade', filename_lower):
        return 'commerce'
    # Restaurant
    elif re.search(r'restaurant|café|bar|brasserie', filename_lower):
        return 'restaurant'
    # Cave
    elif re.search(r'\bcave\b|dépôt|storage', filename_lower):
        return 'cave'
    # Atelier
    elif re.search(r'atelier|workshop', filename_lower):
        return 'atelier'
    # Appartement (default)
    elif re.search(r'appartement|logement|habitation', filename_lower):
        return 'appartement'
    else:
        return 'appartement'  # Default

# Group documents by property
print(f"\n🔄 Analyse des types...")
docs_by_property = {}
for doc in docs:
    prop_id = doc['property_id']
    if prop_id not in docs_by_property:
        docs_by_property[prop_id] = []
    docs_by_property[prop_id].append(doc)

# Analyze types distribution from filenames
type_distribution = {}
for doc in docs:
    detected_type = detect_type_from_filename(doc['file_name'])
    type_distribution[detected_type] = type_distribution.get(detected_type, 0) + 1

print(f"\n📊 Types détectés dans les baux:")
for t, count in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(docs) * 100
    print(f"   {t:20}: {count:3} ({percent:.1f}%)")

# Strategy: Update units based on lease filenames
print(f"\n🔄 Stratégie de mise à jour:")
print(f"   1. Pour chaque unité, chercher son bail correspondant")
print(f"   2. Extraire le type du nom de fichier")
print(f"   3. Mettre à jour la colonne 'type'")

# Get all units with their leases
print(f"\n📦 Chargement des unités et baux...")
all_units = supabase.table("units").select("*").execute().data
all_leases = supabase.table("leases").select("id, unit_id, tenant_id").execute().data
all_tenants = supabase.table("tenants").select("id, name").execute().data

# Create lookups
lease_by_unit = {lease['unit_id']: lease for lease in all_leases}
tenant_by_id = {tenant['id']: tenant for tenant in all_tenants}

print(f"   {len(all_units)} unités")
print(f"   {len(all_leases)} baux")
print(f"   {len(all_tenants)} locataires")

# Match documents to units via tenants
print(f"\n🔍 Matching baux → unités...")
updated = 0
no_match = 0
errors = 0

for unit in all_units:
    try:
        # Get lease for this unit
        lease = lease_by_unit.get(unit['id'])
        if not lease:
            no_match += 1
            continue
        
        # Get tenant name
        tenant = tenant_by_id.get(lease['tenant_id'])
        if not tenant:
            no_match += 1
            continue
        
        tenant_name = tenant['name'].lower()
        
        # Find matching document
        matching_doc = None
        for doc in docs:
            if doc['property_id'] == unit['property_id']:
                doc_name_lower = doc['file_name'].lower()
                # Check if tenant name (or part of it) is in filename
                tenant_words = tenant_name.split()
                matches = sum(1 for word in tenant_words if len(word) > 3 and word in doc_name_lower)
                if matches >= 1:
                    matching_doc = doc
                    break
        
        if matching_doc:
            # Detect type from filename
            detected_type = detect_type_from_filename(matching_doc['file_name'])
            
            # Update unit
            supabase.table("units").update({"type": detected_type}).eq("id", unit['id']).execute()
            updated += 1
            
            if updated % 10 == 0:
                print(f"   ✅ {updated} unités mises à jour...")
        else:
            no_match += 1
            
    except Exception as e:
        errors += 1

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}")
print(f"\n✅ Unités mises à jour: {updated}")
print(f"⚠️  Sans correspondance: {no_match}")
print(f"❌ Erreurs: {errors}")

# Check final state
print(f"\n📊 État final de la colonne 'type':")
units_final = supabase.table("units").select("type").execute().data
type_counts_final = {}
for unit in units_final:
    t = unit.get('type') or 'None'
    type_counts_final[t] = type_counts_final.get(t, 0) + 1

for t, count in sorted(type_counts_final.items(), key=lambda x: x[1], reverse=True):
    percent = count / len(units_final) * 100
    print(f"   {t:20}: {count:3} ({percent:.1f}%)")

print(f"\n✅ Diversité: {len([t for t in type_counts_final if t != 'None'])} catégories")



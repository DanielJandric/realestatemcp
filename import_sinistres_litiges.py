"""
Import sinistres and litiges into Supabase
"""
from supabase import create_client
import pandas as pd
from pathlib import Path
import re
import sys
from datetime import datetime

# Config
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("  IMPORT SINISTRES & LITIGES")
print("="*80)

# Fetch all properties for matching
print("\n1. Loading properties from database...")
props_resp = supabase.table("properties").select("id, name, address, city").execute()
properties = {prop['id']: prop for prop in props_resp.data}
print(f"   Loaded {len(properties)} properties")

# Create property lookup by normalized name
def normalize_name(name):
    """Normalize property names for matching"""
    if not name:
        return ""
    name = str(name).lower().strip()
    # Remove accents
    name = name.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    name = name.replace('à', 'a').replace('â', 'a')
    # Remove common suffixes/prefixes
    name = re.sub(r'\s*-\s*dd\s*$', '', name)
    name = re.sub(r'\s*sion\s*$', '', name)
    name = re.sub(r'\s*martigny\s*$', '', name)
    name = re.sub(r'\s*chippis\s*$', '', name)
    return name.strip()

property_lookup = {}
for prop_id, prop in properties.items():
    key = normalize_name(prop['name'])
    property_lookup[key] = prop_id
    # Also add variations
    if prop['address']:
        addr_key = normalize_name(prop['address'])
        property_lookup[addr_key] = prop_id

def find_property_id(immeuble_name):
    """Find property ID by name or address"""
    normalized = normalize_name(immeuble_name)
    
    # Direct match
    if normalized in property_lookup:
        return property_lookup[normalized]
    
    # Partial match
    for key, prop_id in property_lookup.items():
        if key in normalized or normalized in key:
            return prop_id
    
    # Try word-by-word match
    words = normalized.split()
    for key, prop_id in property_lookup.items():
        key_words = key.split()
        if len(set(words) & set(key_words)) >= 2:  # At least 2 words in common
            return prop_id
    
    return None

def extract_cost(cost_str):
    """Extract numeric cost from string like '1996.7' or "CHF 3'405,35" """
    if pd.isna(cost_str):
        return None
    cost_str = str(cost_str).replace("'", "").replace(",", ".")
    # Extract first number
    match = re.search(r'[\d.]+', cost_str)
    if match:
        try:
            return float(match.group())
        except:
            return None
    return None

def parse_date(date_val):
    """Parse date from various formats"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val.date().isoformat()
    # Try to parse string
    date_str = str(date_val).strip()
    if not date_str or date_str == '-':
        return None
    try:
        dt = pd.to_datetime(date_str)
        return dt.date().isoformat()
    except:
        return None

# ============================================================================
# PART 1: IMPORT SINISTRES
# ============================================================================
print("\n" + "="*80)
print("  IMPORTING SINISTRES")
print("="*80)

# Use only one file to avoid duplicates
sinistre_file = r"Incremental1\Tableau suivi sinistre.xlsx"

try:
    df = pd.read_excel(sinistre_file, sheet_name=0)
    df = df.dropna(how='all')  # Remove empty rows
    
    print(f"\nProcessing {len(df)} sinistres...")
    
    incidents_created = 0
    incidents_skipped = 0
    
    for idx, row in df.iterrows():
        # Skip header rows
        if row.get('N réf') == 'N réf':
            continue
        
        immeuble = row.get('Immeuble')
        if pd.isna(immeuble):
            continue
        
        # Find property
        property_id = find_property_id(immeuble)
        if not property_id:
            print(f"   ⚠️  Property not found for: {immeuble}")
            incidents_skipped += 1
            continue
        
        # Extract data
        ref_num = str(row.get('N réf', '')).strip()
        locataire = str(row.get('Locataire', '')).strip() if pd.notna(row.get('Locataire')) else None
        assurance = str(row.get("Nom de l'assurance", '')).strip() if pd.notna(row.get("Nom de l'assurance")) else None
        date_sinistre = parse_date(row.get('date du sinistre '))
        cause = str(row.get('cause du sinistre ', '')).strip() if pd.notna(row.get('cause du sinistre ')) else None
        statut = str(row.get('Statut ', '')).strip() if pd.notna(row.get('Statut ')) else 'open'
        
        # Map status
        status_map = {
            'terminé': 'closed',
            'en cours': 'in_progress',
            'ouvert': 'open'
        }
        status = status_map.get(statut.lower(), 'open')
        
        # Extract cost
        cost = extract_cost(row.get('coût a charge Investis '))
        
        # Build description
        description_parts = []
        if cause:
            description_parts.append(f"Cause: {cause}")
        if assurance:
            description_parts.append(f"Assurance: {assurance}")
        
        mise_a_jour = row.get('Mise à jour')
        if pd.notna(mise_a_jour) and str(mise_a_jour).strip() != '-':
            description_parts.append(f"Mise à jour: {mise_a_jour}")
        
        commentaires = row.get('Commentaires Investis ')
        if pd.notna(commentaires) and str(commentaires).strip() != '-':
            description_parts.append(f"Commentaires: {commentaires}")
        
        description = "\n\n".join(description_parts) if description_parts else cause
        
        # Create incident (using existing schema columns)
        incident_data = {
            'property_id': property_id,
            'date': date_sinistre or datetime.now().date().isoformat(),
            'description': description,
            'status': status,
            'insurance_ref': assurance,
        }
        
        try:
            supabase.table("incidents").insert(incident_data).execute()
            incidents_created += 1
            prop_name = properties[property_id]['name']
            print(f"   ✅ [{incidents_created}] {prop_name} - {locataire or 'N/A'} ({status})")
        except Exception as e:
            print(f"   ❌ Error inserting incident: {str(e)[:100]}")
            incidents_skipped += 1
    
    print(f"\n✅ Sinistres: {incidents_created} created, {incidents_skipped} skipped")

except Exception as e:
    print(f"❌ Error processing sinistres: {e}")

# ============================================================================
# PART 2: IMPORT LITIGES
# ============================================================================
print("\n" + "="*80)
print("  IMPORTING LITIGES")
print("="*80)

# Use only one file to avoid duplicates
litige_file = r"Incremental1\Litiges.xlsx"

try:
    # Read all sheets
    xl = pd.ExcelFile(litige_file)
    
    disputes_created = 0
    disputes_skipped = 0
    
    for sheet_name in xl.sheet_names:
        print(f"\n Processing sheet: {sheet_name}")
        df = pd.read_excel(litige_file, sheet_name=sheet_name)
        df = df.dropna(how='all')
        
        # Skip if too few rows
        if len(df) < 2:
            continue
        
        # First row is header, skip it
        for idx, row in df.iterrows():
            if idx == 0 or idx == 1:  # Skip header rows
                continue
            
            # Get address
            adresse = row.get('Unnamed: 1') or row.iloc[1] if len(row) > 1 else None
            lieu = row.get('Unnamed: 2') or row.iloc[2] if len(row) > 2 else None
            
            if pd.isna(adresse):
                continue
            
            # Find property
            search_str = f"{adresse} {lieu}".strip()
            property_id = find_property_id(search_str)
            
            if not property_id:
                # Try just address
                property_id = find_property_id(str(adresse))
            
            if not property_id:
                print(f"   ⚠️  Property not found for: {search_str}")
                disputes_skipped += 1
                continue
            
            # Extract data
            locataire = row.get('Unnamed: 3') or row.iloc[3] if len(row) > 3 else None
            motif = row.get('Unnamed: 4') or row.iloc[4] if len(row) > 4 else None
            action = row.get('Unnamed: 5') or row.iloc[5] if len(row) > 5 else None
            remarques = row.get('Unnamed: 6') or row.iloc[6] if len(row) > 6 else None
            
            if pd.isna(locataire):
                continue
            
            locataire = str(locataire).strip()
            motif = str(motif).strip() if pd.notna(motif) else ""
            
            # Build description
            description_parts = []
            if motif:
                description_parts.append(f"Motif: {motif}")
            if action and pd.notna(action):
                description_parts.append(f"Action portée: {action}")
            if remarques and pd.notna(remarques):
                description_parts.append(f"Remarques: {remarques}")
            
            description = "\n\n".join(description_parts) if description_parts else motif
            
            # Determine status based on action
            status = 'open'
            if action and pd.notna(action):
                action_str = str(action).lower()
                if 'tribunal' in action_str or 'conciliation' in action_str:
                    status = 'in_progress'
            
            # Create dispute (using existing schema columns)
            dispute_data = {
                'property_id': property_id,
                'description': description,
                'status': status,
                'date': datetime.now().date().isoformat(),
            }
            
            try:
                supabase.table("disputes").insert(dispute_data).execute()
                disputes_created += 1
                prop_name = properties[property_id]['name']
                print(f"   ✅ [{disputes_created}] {prop_name} - {locataire} ({status})")
            except Exception as e:
                print(f"   ❌ Error inserting dispute: {str(e)[:100]}")
                disputes_skipped += 1
    
    print(f"\n✅ Litiges: {disputes_created} created, {disputes_skipped} skipped")

except Exception as e:
    print(f"❌ Error processing litiges: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("  SUMMARY")
print("="*80)

# Get final counts
incidents = supabase.table("incidents").select("*", count="exact").execute()
disputes = supabase.table("disputes").select("*", count="exact").execute()

print(f"\n📊 Final database counts:")
print(f"   Incidents: {incidents.count}")
print(f"   Disputes: {disputes.count}")

print("\n✅ Import complete!")


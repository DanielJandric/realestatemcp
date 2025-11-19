"""
Link document chunks to properties, units, leases, tenants, etc.
Enriches metadata to enable property-specific search
"""
from supabase import create_client
from pathlib import Path
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

print("="*80)
print("  LINKING EMBEDDINGS → PROPERTIES/UNITS/LEASES")
print("="*80)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get all properties
print("\n📊 Chargement données...")
properties = supabase.table("properties").select("*").execute().data
units = supabase.table("units").select("*").execute().data
leases = supabase.table("leases").select("*").execute().data
tenants = supabase.table("tenants").select("*").execute().data

print(f"✅ {len(properties)} propriétés")
print(f"✅ {len(units)} unités")
print(f"✅ {len(leases)} baux")
print(f"✅ {len(tenants)} locataires")

# Create lookup dictionaries with EXTENSIVE patterns
property_names = {
    'Gare 28': [
        'gare 28', 'gare28', 'gare-28',
        '6053.01.0002', '6053 01 0002',
        'avenue de la gare 28',
        'martigny gare', 'gare martigny',
        '1920 martigny'
    ],
    'Gare 8-10': [
        'gare 8', 'gare 10', 'gare 8-10', 'gare8', 'gare10',
        '6053.01.0001', '6053 01 0001',
        'avenue de la gare 8', 'avenue de la gare 10',
        'martigny'
    ],
    'Place Centrale 3': [
        'place centrale', 'centrale 3', 'place centrale 3',
        '6053.01.0003', '6053 01 0003',
        'martigny place', 'place martigny',
        '1920 martigny'
    ],
    'St-Hubert 1': [
        'st-hubert', 'st hubert', 'saint-hubert', 'saint hubert',
        'hubert 1', 'st-hubert 1',
        '6053.01.0004', '6053 01 0004',
        'martigny hubert'
    ],
    "Pré d'Emoz": [
        'pre emoz', "pré d'emoz", "pre d'emoz", "pré emoz",
        'emoz', 'demoz',
        '6053.01.0005', '6053 01 0005',
        'sion emoz'
    ],
    'Grand Avenue 6': [
        'grand avenue', 'grand-avenue', 'grande avenue',
        'grand avenue 6', 'chippis',
        '6053.01.0006', '6053 01 0006',
        '3965 chippis'
    ],
    'Pratifori 5-7': [
        'pratifori', 'pratifori 5', 'pratifori 7', 'pratifori 5-7',
        'rue de pratifori',
        '45642', '45 642',
        'sion pratifori', '1950 sion'
    ],
    'Banque 4': [
        'banque 4', 'banque4', 'rue de la banque 4',
        'rue de la banque',
        '6053.01.0008', '6053 01 0008',
        'fribourg banque', 'fribourg', '1700 fribourg'
    ]
}

# Build reverse lookup
property_lookup = {}
for prop_name, patterns in property_names.items():
    for pattern in patterns:
        property_lookup[pattern.lower()] = prop_name

# Get property IDs
property_ids = {p['name']: p['id'] for p in properties}

# Get units by property
units_by_property = {}
for unit in units:
    prop_id = unit.get('property_id')
    if prop_id:
        if prop_id not in units_by_property:
            units_by_property[prop_id] = []
        units_by_property[prop_id].append(unit)

# Get leases by unit
leases_by_unit = {}
for lease in leases:
    unit_id = lease.get('unit_id')
    if unit_id:
        if unit_id not in leases_by_unit:
            leases_by_unit[unit_id] = []
        leases_by_unit[unit_id].append(lease)

# Get tenants by ID
tenants_by_id = {t['id']: t for t in tenants}

def detect_property_from_path(file_path):
    """Detect property from file path"""
    path_lower = str(file_path).lower()
    
    for pattern, prop_name in property_lookup.items():
        if pattern in path_lower:
            return prop_name
    
    return None

def detect_property_from_text(text):
    """Detect property from text content"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Score-based detection (multiple patterns = higher confidence)
    scores = {}
    for pattern, prop_name in property_lookup.items():
        if pattern in text_lower:
            scores[prop_name] = scores.get(prop_name, 0) + 1
    
    if scores:
        # Return property with highest score
        return max(scores, key=scores.get)
    
    return None

def detect_unit_number(text):
    """Extract unit number from text"""
    # Patterns: "App. 12", "Appt 3.05", "Wohnung 405", etc.
    patterns = [
        r'app(?:artement)?\.?\s*(\d+(?:\.\d+)?)',
        r'wohnung\s*(\d+(?:\.\d+)?)',
        r'unit\s*(\d+(?:\.\d+)?)',
        r'parking\s*(?:n°|nr\.?)?\s*(\d+)',
        r'place\s*(?:n°|nr\.?)?\s*(\d+)',
        r'bureau\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    
    return None

def detect_tenant_name(text, chunk_text):
    """Detect tenant from text"""
    # Look for tenant names in chunk
    for tenant in tenants:
        tenant_name = tenant.get('name', '').lower()
        if tenant_name and len(tenant_name) > 5:
            if tenant_name in chunk_text.lower():
                return tenant['id'], tenant_name
    
    return None, None

# Get all document chunks
print("\n📄 Récupération chunks...")
chunks = supabase.table("document_chunks").select("id, document_id, chunk_text, metadata").execute().data
print(f"✅ {len(chunks)} chunks à analyser\n")

# Get documents
print("📁 Récupération documents...")
documents = supabase.table("documents").select("id, file_path, file_name, category").execute().data
docs_by_id = {d['id']: d for d in documents}
print(f"✅ {len(documents)} documents\n")

# Process chunks
print("="*80)
print("  ANALYSE ET LINKING")
print("="*80)

linked_count = 0
updated_count = 0

from tqdm import tqdm

for chunk in tqdm(chunks, desc="Linking"):
    try:
        chunk_id = chunk['id']
        document_id = chunk.get('document_id')
        chunk_text = chunk.get('chunk_text', '')
        current_metadata = chunk.get('metadata') or {}
        
        # Skip if already linked
        if current_metadata.get('property_id'):
            linked_count += 1
            continue
        
        # Get document info
        document = docs_by_id.get(document_id) if document_id else None
        file_path = document.get('file_path', '') if document else ''
        
        # Detect property
        property_name = None
        
        # 1. Try from file path (if exists)
        if file_path:
            property_name = detect_property_from_path(file_path)
        
        # 2. Try from text content (ALWAYS, even if path worked)
        if chunk_text:
            text_property = detect_property_from_text(chunk_text)
            # If both found and different, prefer text (more accurate)
            if text_property:
                property_name = text_property
        
        # If property found, enrich metadata
        if property_name and property_name in property_ids:
            property_id = property_ids[property_name]
            
            # Build enriched metadata
            enriched_metadata = {
                **current_metadata,
                'property_id': property_id,
                'property_name': property_name,
            }
            
            # Try to detect unit
            unit_number = detect_unit_number(chunk_text) if chunk_text else None
            if unit_number:
                enriched_metadata['unit_number'] = unit_number
                
                # Try to find exact unit
                prop_units = units_by_property.get(property_id, [])
                for unit in prop_units:
                    if unit.get('unit_number') == unit_number:
                        enriched_metadata['unit_id'] = unit['id']
                        
                        # Get lease for this unit
                        unit_leases = leases_by_unit.get(unit['id'], [])
                        if unit_leases:
                            # Get most recent active lease
                            active_lease = None
                            for lease in unit_leases:
                                if lease.get('status') == 'active':
                                    active_lease = lease
                                    break
                            
                            if not active_lease and unit_leases:
                                active_lease = unit_leases[0]
                            
                            if active_lease:
                                enriched_metadata['lease_id'] = active_lease['id']
                                
                                # Get tenant
                                tenant_id = active_lease.get('tenant_id')
                                if tenant_id and tenant_id in tenants_by_id:
                                    tenant = tenants_by_id[tenant_id]
                                    enriched_metadata['tenant_id'] = tenant_id
                                    enriched_metadata['tenant_name'] = tenant.get('name')
                        
                        break
            
            # Detect tenant from text (fallback)
            if not enriched_metadata.get('tenant_id') and chunk_text:
                tenant_id, tenant_name = detect_tenant_name(file_path, chunk_text)
                if tenant_id:
                    enriched_metadata['tenant_id'] = tenant_id
                    enriched_metadata['tenant_name'] = tenant_name
            
            # Update chunk metadata
            supabase.table("document_chunks").update({
                'metadata': enriched_metadata
            }).eq('id', chunk_id).execute()
            
            updated_count += 1
        
    except Exception as e:
        continue

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Chunks déjà liés: {linked_count}")
print(f"✅ Chunks mis à jour: {updated_count}")
print(f"📊 Total chunks: {len(chunks)}")
print(f"📊 Taux de linking: {((linked_count + updated_count) / len(chunks) * 100):.1f}%")

# Statistics
print(f"\n{'='*80}")
print(f"  STATISTIQUES PAR PROPRIÉTÉ")
print(f"{'='*80}\n")

# Re-fetch to get updated stats
chunks_updated = supabase.table("document_chunks").select("metadata").execute().data

from collections import Counter
property_counts = Counter()

for chunk in chunks_updated:
    metadata = chunk.get('metadata') or {}
    prop_name = metadata.get('property_name')
    if prop_name:
        property_counts[prop_name] += 1

for prop_name, count in property_counts.most_common():
    print(f"  {prop_name:25} : {count:>6,} chunks")

if property_counts:
    unlinked = len(chunks) - sum(property_counts.values())
    print(f"  {'(Non liés)':25} : {unlinked:>6,} chunks")

print(f"\n✅ Linking terminé!\n")

print("📋 MAINTENANT VOUS POUVEZ:")
print("  • Recherche par propriété: metadata->property_name = 'Gare 28'")
print("  • Recherche par unité: metadata->unit_number = '3.05'")
print("  • Recherche par locataire: metadata->tenant_name = 'Dupont'")
print("  • Recherche sémantique enrichie avec filtres\n")


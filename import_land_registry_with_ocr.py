"""
Import Land Registry Documents with OCR and Smart Extraction
Focuses on servitudes, restrictions, and land registry extracts
"""
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv
import hashlib
from tqdm import tqdm
import re
from datetime import datetime

load_dotenv()

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or "your_openai_api_key_here"

AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

ROOT_DIR = Path(r"C:\OneDriveExport")

print("="*80)
print("  IMPORT REGISTRE FONCIER & SERVITUDES")
print("="*80 + "\n")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Azure OCR
if AZURE_ENDPOINT and AZURE_KEY:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    azure_client = DocumentAnalysisClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_KEY)
    )
    print("[OK] Azure OCR disponible\n")
else:
    print("[ERROR] Azure OCR requis pour ce script!")
    exit(1)

# Property mapping
property_map = {
    'Pratifori 5-7': {'name': 'Pratifori 5-7', 'patterns': ['pratifori', '45642']},
    'Gare 28': {'name': 'Gare 28', 'patterns': ['gare 28', '6053.01.0002']},
    'Gare 8-10': {'name': 'Gare 8-10', 'patterns': ['gare 8', 'gare 10']},
    'Place Centrale 3': {'name': 'Place Centrale 3', 'patterns': ['centrale 3', 'place centrale']},
    'St-Hubert 1': {'name': 'St-Hubert 1', 'patterns': ['st-hubert', 'hubert 5']},
    "Pré d'Emoz": {'name': "Pré d'Emoz", 'patterns': ['pre emoz', "pré d'emoz", 'aigle']},
    'Grand Avenue 6': {'name': 'Grand Avenue 6', 'patterns': ['grand avenue', 'chippis']},
    'Banque 4': {'name': 'Banque 4', 'patterns': ['banque 4', 'fribourg']}
}

# Get properties from DB
properties = supabase.table("properties").select("*").execute().data
properties_by_name = {p['name']: p['id'] for p in properties}

def detect_property(file_path):
    """Detect property from path"""
    path_lower = str(file_path).lower()
    for prop_name, prop_data in property_map.items():
        for pattern in prop_data['patterns']:
            if pattern.lower() in path_lower:
                return prop_name, properties_by_name.get(prop_name)
    return None, None

def classify_document(file_name, text_sample):
    """Classify type of land registry document"""
    name_lower = file_name.lower()
    text_lower = text_sample.lower() if text_sample else ""
    
    # Servitudes et restrictions
    if any(x in name_lower for x in ['restriction', 'servitude', 'charge', 'gage']):
        return 'restrictions'
    
    # Règlements
    if any(x in name_lower for x in ['règlement', 'reglement']):
        return 'reglement_construction'
    
    # Plans
    if any(x in name_lower for x in ['plan', 'zone', 'affectation', 'cadastre']):
        return 'plan_affectation'
    
    # Extraits RF (avec année généralement)
    if 'registre' in name_lower or re.search(r'\d{4}-\d{5}', file_name):
        return 'extrait_rf'
    
    return 'extrait_rf'  # Par défaut

def extract_servitudes_from_text(text):
    """Extract servitudes from text using patterns"""
    servitudes = []
    
    # Patterns pour détecter servitudes
    servitude_patterns = [
        r'servitude\s+de\s+(\w+)',
        r'droit\s+de\s+(\w+)',
        r'restriction\s+(?:de|à)\s+([\w\s]+)',
        r'charge\s+(?:de|à)\s+([\w\s]+)',
        r'interdiction\s+de\s+([\w\s]+)'
    ]
    
    for pattern in servitude_patterns:
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            context_start = max(0, match.start() - 200)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]
            
            servitudes.append({
                'type': match.group(1) if match.groups() else 'indéterminé',
                'context': context.strip(),
                'position': match.start()
            })
    
    return servitudes

def extract_parcelle_info(text):
    """Extract parcel information"""
    info = {}
    
    # Numéro de parcelle
    parcelle_match = re.search(r'parcelle\s+n[°o]?\s*(\d+)', text.lower())
    if parcelle_match:
        info['numero_parcelle'] = parcelle_match.group(1)
    
    # Bien-fonds
    bf_match = re.search(r'bien-fonds\s+n[°o]?\s*(\d+)', text.lower())
    if bf_match:
        info['numero_bien_fonds'] = bf_match.group(1)
    
    # Surface
    surface_match = re.search(r'surface[:\s]+(\d+(?:[\.,]\d+)?)\s*m', text.lower())
    if surface_match:
        info['surface'] = float(surface_match.group(1).replace(',', '.'))
    
    # Zone
    zone_matches = re.findall(r'zone\s+(?:de\s+)?(\w+(?:\s+\w+)?)', text.lower())
    if zone_matches:
        info['zone'] = zone_matches[0]
    
    return info

# Find all land registry folders
print("[1/4] Scan dossiers Registre Foncier...")
rf_folders = []

for root, dirs, files in os.walk(ROOT_DIR):
    if 'registre foncier' in root.lower() or 'cadastre' in root.lower():
        # Get PDF files in this folder
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        if pdf_files:
            rf_folders.append({
                'path': Path(root),
                'files': pdf_files
            })

print(f"✅ {len(rf_folders)} dossiers trouvés\n")

# Count total files
total_files = sum(len(folder['files']) for folder in rf_folders)
print(f"📄 {total_files} fichiers PDF à traiter\n")

# Process files
print("[2/4] Traitement OCR et extraction...")
processed = 0
documents_created = 0
servitudes_found = 0

for folder_info in tqdm(rf_folders, desc="Dossiers"):
    folder_path = folder_info['path']
    
    for file_name in folder_info['files']:
        file_path = folder_path / file_name
        
        try:
            # Detect property
            prop_name, prop_id = detect_property(file_path)
            
            # OCR
            with open(file_path, "rb") as f:
                poller = azure_client.begin_analyze_document("prebuilt-document", document=f)
                result = poller.result()
            
            # Extract text
            text = ""
            for page in result.pages:
                for line in page.lines:
                    text += line.content + "\n"
            
            if not text or len(text) < 50:
                continue
            
            # Classify
            doc_type = classify_document(file_name, text[:500])
            
            # Create document entry
            doc_data = {
                'file_path': str(file_path),
                'file_name': file_name,
                'file_type': 'pdf',
                'category': 'land_registry',
                'property_id': prop_id
            }
            
            doc_result = supabase.table("documents").insert(doc_data).execute()
            document_id = doc_result.data[0]['id']
            documents_created += 1
            
            # Create land_registry_document entry
            parcelle_info = extract_parcelle_info(text)
            
            lrd_data = {
                'property_id': prop_id,
                'document_id': document_id,
                'document_type': doc_type,
                'numero_parcelle': parcelle_info.get('numero_parcelle'),
                'numero_bien_fonds': parcelle_info.get('numero_bien_fonds'),
                'surface_totale': parcelle_info.get('surface'),
                'zone_affectation': parcelle_info.get('zone'),
                'date_extrait': datetime.now().date().isoformat()
            }
            
            supabase.table("land_registry_documents").insert(lrd_data).execute()
            
            # Extract servitudes if it's a restriction document
            if doc_type == 'restrictions' or 'servitude' in text.lower():
                servitudes_list = extract_servitudes_from_text(text)
                
                for serv in servitudes_list[:10]:  # Limit to avoid duplicates
                    servitude_data = {
                        'property_id': prop_id,
                        'type_servitude': 'servitude',
                        'description': serv['context'][:500],
                        'document_source_id': document_id,
                        'extrait_texte': serv['context'],
                        'statut': 'active',
                        'importance_niveau': 'normale'
                    }
                    
                    supabase.table("servitudes").insert(servitude_data).execute()
                    servitudes_found += 1
            
            processed += 1
            
        except Exception as e:
            print(f"\n⚠️  Erreur {file_name}: {e}")
            continue

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Fichiers traités: {processed}")
print(f"✅ Documents créés: {documents_created}")
print(f"✅ Servitudes identifiées: {servitudes_found}")

# Generate embeddings
print(f"\n[3/4] Génération embeddings...")
import openai
openai.api_key = OPENAI_API_KEY

# [Code embeddings would go here - similar to embed_delta_only.py]
print("⏭️  Skipped pour cette première version - à faire séparément\n")

print("[4/4] Statistiques finales...")

# Count by property
lrd_by_prop = supabase.table("land_registry_documents").select("property_id", count="exact").execute()
serv_by_prop = supabase.table("servitudes").select("property_id", count="exact").execute()

print(f"\n{'='*80}")
print(f"  PAR PROPRIÉTÉ")
print(f"{'='*80}\n")

for prop_name in property_map.keys():
    prop_id = properties_by_name.get(prop_name)
    if prop_id:
        lrd_count = len([d for d in lrd_by_prop.data if d.get('property_id') == prop_id])
        serv_count = len([s for s in serv_by_prop.data if s.get('property_id') == prop_id])
        print(f"  {prop_name:25s}: {lrd_count} docs RF, {serv_count} servitudes")

print(f"\n🎉 Import registre foncier terminé!")
print(f"   Prochaine étape: Analyse manuelle des servitudes critiques\n")


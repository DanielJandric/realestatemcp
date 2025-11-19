"""
Extract detailed insurance data from PDFs using Azure Document Intelligence OCR
"""
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv
import re
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check for Azure credentials
AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

if not AZURE_ENDPOINT or not AZURE_KEY:
    print("❌ Erreur: Variables Azure non trouvées dans .env")
    print("   Requis: AZURE_DOC_INTELLIGENCE_ENDPOINT et AZURE_DOC_INTELLIGENCE_KEY")
    exit(1)

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

print("="*80)
print("  EXTRACTION DÉTAILLÉE DES POLICES D'ASSURANCE")
print("="*80)
print(f"\n✅ Azure Document Intelligence connecté")

# Insurance files to process
insurance_files = [
    {
        'file': Path(r"Incremental1\Propositions d'assurance\Polices d'assurances\Police du 01.02.2024 au 01.02.2029 - Be Capital SA - Sion.pdf"),
        'properties': ['Gare 28', 'St-Hubert'],
        'main_property': 'Gare 28',
        'insurer': 'Be Capital SA',
        'policy_type': 'property'
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\Polices d'assurances\Police du 01.02.2024 au 01.02.2029 - Be Capital SA - Aigle.pdf"),
        'properties': ["Pre d'Emoz"],
        'main_property': "Pre d'Emoz",
        'insurer': 'Be Capital SA',
        'policy_type': 'property'
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\Polices d'assurances\Police du 08.02.2024 au 01.02.2029 - Audacia Management Sàrl - Martigny.pdf"),
        'properties': ['Gare 8-10', 'Place Centrale 3'],
        'main_property': 'Gare 8-10',
        'insurer': 'Audacia Management Sàrl',
        'policy_type': 'property'
    },
    {
        'file': Path(r'Incremental1\St-Hubert 5 - Sion - DD\02. Assurances\Baloise\Police du 01.01.2025 au 31.12.2027.pdf'),
        'properties': ['St-Hubert'],
        'main_property': 'St-Hubert',
        'insurer': 'Baloise',
        'policy_type': 'building'
    }
]

# Additional insurance files from St-Hubert Baloise
st_hubert_assurance_dir = Path(r'Incremental1\St-Hubert 5 - Sion - DD\02. Assurances')
if st_hubert_assurance_dir.exists():
    for pdf in st_hubert_assurance_dir.rglob('*.pdf'):
        if 'police' not in pdf.name.lower():
            insurance_files.append({
                'file': pdf,
                'properties': ['St-Hubert'],
                'main_property': 'St-Hubert',
                'insurer': 'Baloise',
                'policy_type': 'building'
            })

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using Azure OCR"""
    try:
        with open(pdf_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document(
                "prebuilt-document", document=f
            )
            result = poller.result()
        
        full_text = ""
        for page in result.pages:
            for line in page.lines:
                full_text += line.content + "\n"
        
        return full_text
    except Exception as e:
        print(f"      ❌ Erreur OCR: {str(e)}")
        return ""

def extract_currency_amount(text, keywords):
    """Extract currency amounts (CHF, EUR) near keywords"""
    amounts = []
    
    for keyword in keywords:
        # Look for patterns like "keyword ... 1'234'567.89 CHF" or "CHF 1'234'567.89"
        pattern = rf"{keyword}[^\d]*?([\d']+(?:\.\d{{2}})?)\s*(?:CHF|Fr\.|francs)"
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            amount_str = match.group(1).replace("'", "").replace(" ", "")
            try:
                amount = float(amount_str)
                amounts.append(amount)
            except:
                pass
    
    return max(amounts) if amounts else None

def extract_policy_number(text):
    """Extract policy number"""
    # Common patterns for policy numbers
    patterns = [
        r'[Pp]olice\s*(?:n[°o]?|numéro)\s*[:\s]*([A-Z0-9\-\.]+)',
        r'[Cc]ontrat\s*(?:n[°o]?|numéro)\s*[:\s]*([A-Z0-9\-\.]+)',
        r'[Nn]°\s*de\s*police\s*[:\s]*([A-Z0-9\-\.]+)',
        r'Policy\s*(?:No|Number)\s*[:\s]*([A-Z0-9\-\.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return None

def extract_deductible(text):
    """Extract deductible amount or percentage"""
    # Look for franchise/deductible
    patterns = [
        r"[Ff]ranchise[^\d]*?([\d']+(?:\.\d{2})?)\s*(?:CHF|Fr\.)",
        r"[Dd]éductible[^\d]*?([\d']+(?:\.\d{2})?)\s*(?:CHF|Fr\.)",
        r'[Ff]ranchise[^\d]*?(\d+)\s*%'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace("'", "").replace(" ", "")
            try:
                if '%' in pattern:
                    return None, float(value_str)  # percentage
                else:
                    return float(value_str), None  # amount
            except:
                pass
    
    return None, None

def extract_coverage_types(text):
    """Detect what types of coverage are included"""
    coverage = {
        'fire': False,
        'water_damage': False,
        'natural_disasters': False,
        'theft': False,
        'liability': False,
        'rental_loss': False,
        'terrorism': False
    }
    
    keywords = {
        'fire': ['incendie', 'feu'],
        'water_damage': ['dégât d\'eau', 'dégâts des eaux', 'eau'],
        'natural_disasters': ['catastrophe naturelle', 'forces de la nature', 'éléments naturels'],
        'theft': ['vol', 'effraction'],
        'liability': ['responsabilité civile', 'RC'],
        'rental_loss': ['perte de loyer', 'pertes de loyers', 'privation de jouissance'],
        'terrorism': ['terrorisme', 'actes terroristes']
    }
    
    text_lower = text.lower()
    for coverage_type, terms in keywords.items():
        for term in terms:
            if term in text_lower:
                coverage[coverage_type] = True
                break
    
    return coverage

# Get all properties
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

# Get existing policies
existing_policies = supabase.table("insurance_policies").select("id, property_id").execute().data
policy_by_property = {p['property_id']: p['id'] for p in existing_policies}

print(f"\n📄 Traitement de {len(insurance_files)} fichiers...\n")

updates_by_property = {}

for idx, file_info in enumerate(insurance_files, 1):
    file_path = file_info['file']
    
    if not file_path.exists():
        print(f"\n   ❌ Fichier non trouvé: {file_path.name}")
        continue
    
    print(f"{'='*80}")
    print(f"📄 [{idx}/{len(insurance_files)}] {file_path.name}")
    print(f"{'='*80}")
    
    # Extract text with OCR
    print(f"   🔍 Extraction OCR...")
    text = extract_text_from_pdf(file_path)
    
    if not text:
        print(f"   ❌ Pas de texte extrait")
        continue
    
    print(f"   ✅ {len(text)} caractères extraits")
    
    # Extract data
    print(f"\n   📊 Analyse des données...")
    
    policy_number = extract_policy_number(text)
    
    # Extract financial values
    insured_value = extract_currency_amount(text, [
        'valeur à neuf', 'valeur assurée', 'somme assurée', 'capital assuré',
        'total assuré', 'montant assuré'
    ])
    
    building_value = extract_currency_amount(text, [
        'bâtiment', 'immeuble', 'valeur du bâtiment'
    ])
    
    contents_value = extract_currency_amount(text, [
        'contenu', 'mobilier', 'installations'
    ])
    
    rental_loss = extract_currency_amount(text, [
        'perte de loyer', 'pertes de loyers', 'privation de jouissance'
    ])
    
    annual_premium = extract_currency_amount(text, [
        'prime annuelle', 'prime totale', 'coût annuel', 'prime nette'
    ])
    
    deductible_amount, deductible_pct = extract_deductible(text)
    
    coverage = extract_coverage_types(text)
    
    # Build update data
    update_data = {}
    
    if policy_number:
        update_data['policy_number'] = policy_number
        print(f"      • N° Police: {policy_number}")
    
    if annual_premium:
        update_data['annual_premium'] = round(annual_premium, 2)
        print(f"      • Prime annuelle: {annual_premium:,.2f} CHF")
    
    if insured_value:
        update_data['insured_value'] = round(insured_value, 2)
        print(f"      • Valeur assurée totale: {insured_value:,.0f} CHF")
    
    if building_value:
        update_data['building_value'] = round(building_value, 2)
        print(f"      • Valeur bâtiment: {building_value:,.0f} CHF")
    
    if contents_value:
        update_data['contents_value'] = round(contents_value, 2)
        print(f"      • Valeur contenu: {contents_value:,.0f} CHF")
    
    if rental_loss:
        update_data['rental_loss_coverage'] = round(rental_loss, 2)
        print(f"      • Couverture perte loyer: {rental_loss:,.0f} CHF")
    
    if deductible_amount:
        update_data['deductible_amount'] = round(deductible_amount, 2)
        print(f"      • Franchise: {deductible_amount:,.2f} CHF")
    
    if deductible_pct:
        update_data['deductible_percentage'] = round(deductible_pct, 2)
        print(f"      • Franchise: {deductible_pct}%")
    
    # Coverage flags
    if coverage['rental_loss']:
        update_data['loss_of_rent_covered'] = True
    if coverage['natural_disasters']:
        update_data['natural_disasters_covered'] = True
    if coverage['terrorism']:
        update_data['terrorism_covered'] = True
    
    # Build coverage description
    covered_types = [k.replace('_', ' ').title() for k, v in coverage.items() if v]
    if covered_types:
        update_data['description'] = f"Couvertures: {', '.join(covered_types)}"
        print(f"      • Couvertures: {', '.join(covered_types)}")
    
    # Update insurer if we found more info
    if file_info['insurer'] != 'À déterminer':
        update_data['insurer_name'] = file_info['insurer']
    
    update_data['status'] = 'active'
    
    # Store updates for each property
    for prop_name in file_info['properties']:
        if prop_name in property_by_name:
            prop_id = property_by_name[prop_name]
            if prop_id not in updates_by_property:
                updates_by_property[prop_id] = []
            updates_by_property[prop_id].append({
                'property_id': prop_id,
                'property_name': prop_name,
                'update_data': update_data.copy(),
                'file': file_path.name
            })
    
    print()

# Apply updates
print(f"\n{'='*80}")
print(f"  APPLICATION DES MISES À JOUR")
print(f"{'='*80}\n")

total_updated = 0

for prop_id, updates_list in updates_by_property.items():
    if prop_id in policy_by_property:
        policy_id = policy_by_property[prop_id]
        
        # Merge all updates for this property
        merged_update = {'updated_at': datetime.now().isoformat()}
        for update_info in updates_list:
            merged_update.update(update_info['update_data'])
        
        # Update the policy
        try:
            supabase.table("insurance_policies").update(merged_update).eq("id", policy_id).execute()
            prop_name = updates_list[0]['property_name']
            print(f"   ✅ {prop_name}: {len(merged_update)-1} champs mis à jour")
            total_updated += 1
        except Exception as e:
            print(f"   ❌ Erreur pour {prop_name}: {str(e)}")

print(f"\n{'='*80}")
print(f"  RÉSUMÉ FINAL")
print(f"{'='*80}\n")

print(f"   ✅ {total_updated} polices mises à jour")

# Final statistics
all_policies = supabase.table("insurance_policies").select("*").execute().data

complete_fields = {
    'policy_number': 0,
    'annual_premium': 0,
    'insured_value': 0,
    'building_value': 0,
    'deductible_amount': 0
}

for pol in all_policies:
    for field in complete_fields:
        if pol.get(field) and (isinstance(pol[field], str) or pol[field] > 0):
            complete_fields[field] += 1

print(f"\n📊 Complétude des données:")
for field, count in complete_fields.items():
    pct = (count / len(all_policies) * 100) if all_policies else 0
    print(f"   {field:25} : {count:>2}/{len(all_policies):<2} ({pct:>5.1f}%)")

print(f"\n✅ Extraction et mise à jour terminées!\n")


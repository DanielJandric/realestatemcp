"""
Final comprehensive insurance extraction with improved parsing
"""
from supabase import create_client
from pathlib import Path
import os
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

print("="*80)
print("  EXTRACTION FINALE - ASSURANCES")
print("="*80)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        with open(pdf_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document("prebuilt-document", document=f)
            result = poller.result()
        
        full_text = ""
        for page in result.pages:
            for line in page.lines:
                full_text += line.content + "\n"
        
        return full_text
    except Exception as e:
        return ""

def parse_amount(text):
    """Parse Swiss franc amount like 6'110.80 or 6 110.80"""
    # Remove spaces and apostrophes, keep only digits and decimal point
    cleaned = text.replace("'", "").replace(" ", "").strip()
    try:
        return float(cleaned)
    except:
        return None

def extract_structured_data(text):
    """Extract structured data from insurance document"""
    data = {}
    lines = text.split('\n')
    
    # Extract policy number
    for i, line in enumerate(lines):
        if 'numéro de proposition' in line.lower() or 'proposition' in line.lower():
            # Look in next few lines
            for j in range(i, min(i+5, len(lines))):
                match = re.search(r'\d{6}[-\.]\d+[-\.]\d+[-\.]\d+[-\.]\d+', lines[j])
                if match:
                    data['policy_number'] = match.group(0)
                    break
    
    # Extract annual premium - look for "Prime annuelle" followed by amount
    for i, line in enumerate(lines):
        if 'prime annuelle' in line.lower() and 'conclusion' in line.lower():
            # Look for CHF amount in next 3 lines
            for j in range(i, min(i+4, len(lines))):
                if 'CHF' in lines[j]:
                    # Next line might have the amount
                    if j+1 < len(lines):
                        amount = parse_amount(lines[j+1])
                        if amount and amount > 100:
                            data['annual_premium'] = amount
                            break
                # Or same line
                match = re.search(r'CHF\s+([\d\'\s]+\.?\d*)', lines[j])
                if match:
                    amount = parse_amount(match.group(1))
                    if amount and amount > 100:
                        data['annual_premium'] = amount
                        break
    
    # Extract insured values - look for "Somme assurée" sections
    values = {
        'building': [],
        'contents': [],
        'total': []
    }
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Building value
        if 'bâtiment' in line_lower and 'somme assurée' in line_lower:
            for j in range(i, min(i+5, len(lines))):
                match = re.search(r'CHF\s+([\d\'\s]+\.?\d*)', lines[j])
                if match:
                    amount = parse_amount(match.group(1))
                    if amount and amount > 10000:
                        values['building'].append(amount)
                        break
        
        # Contents value
        if ('contenu' in line_lower or 'mobilier' in line_lower) and 'somme assurée' in line_lower:
            for j in range(i, min(i+5, len(lines))):
                match = re.search(r'CHF\s+([\d\'\s]+\.?\d*)', lines[j])
                if match:
                    amount = parse_amount(match.group(1))
                    if amount and amount > 1000:
                        values['contents'].append(amount)
                        break
        
        # Total insured
        if 'total' in line_lower and ('somme' in line_lower or 'assurée' in line_lower):
            for j in range(i, min(i+5, len(lines))):
                match = re.search(r'CHF\s+([\d\'\s]+\.?\d*)', lines[j])
                if match:
                    amount = parse_amount(match.group(1))
                    if amount and amount > 10000:
                        values['total'].append(amount)
                        break
    
    # Take largest values
    if values['building']:
        data['building_value'] = max(values['building'])
    if values['contents']:
        data['contents_value'] = max(values['contents'])
    if values['total']:
        data['insured_value'] = max(values['total'])
    
    # Extract franchise
    for i, line in enumerate(lines):
        if 'franchise' in line.lower():
            match = re.search(r'CHF\s+([\d\'\s]+\.?\d*)', line)
            if match:
                amount = parse_amount(match.group(1))
                if amount:
                    data['deductible_amount'] = amount
            
            match_pct = re.search(r'(\d+)\s*%', line)
            if match_pct:
                data['deductible_percentage'] = float(match_pct.group(1))
    
    return data

# Proposals to process
proposals = [
    {
        'file': Path(r"Incremental1\Propositions d'assurance\PROP DU 25.01.2024-Audacia_Management_Sarl_119567-1-601-566-109 (3).pdf"),
        'properties': ['Gare 8-10', 'Place Centrale 3']
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\PROP DU 25.01.2024-Be_Capital_SA_119567-1-601-568-342 (5).pdf"),
        'properties': ['Gare 28', 'St-Hubert']
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\PROP du 25.01.2024-Be_Capital_SA_119567-1-601-569-719 (3).pdf"),
        'properties': ["Pre d'Emoz"]
    }
]

# Get properties
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

# Get existing policies  
existing_policies = supabase.table("insurance_policies").select("id, property_id").execute().data
policy_by_property = {p['property_id']: p['id'] for p in existing_policies}

print(f"\n📄 Extraction de {len(proposals)} propositions...\n")

updates_by_property = {}

for idx, proposal_info in enumerate(proposals, 1):
    file_path = proposal_info['file']
    
    if not file_path.exists():
        print(f"❌ Non trouvé: {file_path.name}")
        continue
    
    print(f"{'='*80}")
    print(f"[{idx}/{len(proposals)}] {file_path.name}")
    print(f"{'='*80}")
    
    text = extract_text_from_pdf(file_path)
    
    if not text:
        print("❌ Échec extraction")
        continue
    
    print(f"✅ {len(text)} caractères extraits")
    
    # Parse structured data
    data = extract_structured_data(text)
    
    if data:
        print(f"\n📊 Données extraites:")
        for field, value in data.items():
            if isinstance(value, float):
                if 'value' in field or 'premium' in field or 'amount' in field:
                    print(f"   • {field:25} : {value:>15,.2f} CHF")
                else:
                    print(f"   • {field:25} : {value:>15,.2f}")
            else:
                print(f"   • {field:25} : {value}")
        
        # Store for each property
        for prop_name in proposal_info['properties']:
            if prop_name in property_by_name:
                prop_id = property_by_name[prop_name]
                if prop_id not in updates_by_property:
                    updates_by_property[prop_id] = {}
                updates_by_property[prop_id].update(data)
    else:
        print("⚠️  Aucune donnée structurée extraite")
    
    print()

# Apply updates
print(f"{'='*80}")
print(f"  MISE À JOUR")
print(f"{'='*80}\n")

updated_count = 0

for prop_id, update_data in updates_by_property.items():
    if prop_id in policy_by_property:
        policy_id = policy_by_property[prop_id]
        
        # Find property name
        prop_name = next((p['name'] for p in properties if p['id'] == prop_id), 'Unknown')
        
        try:
            update_data['updated_at'] = datetime.now().isoformat()
            update_data['status'] = 'active'
            supabase.table("insurance_policies").update(update_data).eq("id", policy_id).execute()
            print(f"✅ {prop_name}: {len(update_data)-2} champs mis à jour")
            updated_count += 1
        except Exception as e:
            print(f"❌ {prop_name}: {str(e)}")

# Final statistics
print(f"\n{'='*80}")
print(f"  STATISTIQUES FINALES")
print(f"{'='*80}\n")

all_policies = supabase.table("insurance_policies").select("*").execute().data

stats = {
    'policy_number': 0,
    'annual_premium': 0,
    'insured_value': 0,
    'building_value': 0,
    'contents_value': 0,
    'rental_loss_coverage': 0,
    'deductible_amount': 0,
    'deductible_percentage': 0
}

total_premium = 0
total_insured = 0

for pol in all_policies:
    for field in stats:
        if pol.get(field) and (isinstance(pol[field], str) or pol[field] > 0):
            stats[field] += 1
    
    if pol.get('annual_premium'):
        total_premium += pol['annual_premium']
    if pol.get('insured_value'):
        total_insured += pol['insured_value']
    elif pol.get('building_value'):
        total_insured += pol['building_value']

print(f"📊 Complétude:")
for field, count in stats.items():
    pct = (count / len(all_policies) * 100) if all_policies else 0
    bar = '█' * int(pct/5) + '░' * (20 - int(pct/5))
    print(f"   {field:25} [{bar}] {pct:>5.1f}% ({count}/{len(all_policies)})")

if total_premium > 0:
    print(f"\n💰 Coût total des primes: {total_premium:>20,.2f} CHF/an")

if total_insured > 0:
    print(f"🏢 Valeurs assurées:      {total_insured:>20,.0f} CHF")

print(f"\n✅ {updated_count} polices mises à jour")
print(f"✅ Extraction finalisée!\n")



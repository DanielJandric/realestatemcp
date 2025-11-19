"""
Extract detailed financial data from insurance PROPOSALS (PROP files)
These contain more detailed breakdowns than the generic policies
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

if not AZURE_ENDPOINT or not AZURE_KEY:
    print("❌ Erreur: Variables Azure non trouvées")
    exit(1)

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

print("="*80)
print("  EXTRACTION PROPOSITIONS D'ASSURANCE")
print("="*80)

# Proposal files
proposals = [
    {
        'file': Path(r"Incremental1\Propositions d'assurance\PROP DU 25.01.2024-Audacia_Management_Sarl_119567-1-601-566-109 (3).pdf"),
        'properties': ['Gare 8-10', 'Place Centrale 3'],
        'insurer': 'Audacia Management Sàrl'
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\PROP DU 25.01.2024-Be_Capital_SA_119567-1-601-568-342 (5).pdf"),
        'properties': ['Gare 28', 'St-Hubert'],
        'insurer': 'Be Capital SA'
    },
    {
        'file': Path(r"Incremental1\Propositions d'assurance\PROP du 25.01.2024-Be_Capital_SA_119567-1-601-569-719 (3).pdf"),
        'properties': ["Pre d'Emoz"],
        'insurer': 'Be Capital SA'
    }
]

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

def extract_all_amounts(text):
    """Extract all CHF amounts from text with their context"""
    # Find all amounts with surrounding context
    pattern = r"(.{0,50})([\d'\s]+(?:\.\d{2})?)\s*(?:CHF|Fr\.|francs)(.{0,50})"
    matches = re.finditer(pattern, text, re.IGNORECASE)
    
    amounts = []
    for match in matches:
        before = match.group(1).strip()
        amount_str = match.group(2).replace("'", "").replace(" ", "")
        after = match.group(3).strip()
        
        try:
            amount = float(amount_str)
            if amount > 100:  # Ignore small amounts
                amounts.append({
                    'amount': amount,
                    'before': before[-50:],
                    'after': after[:50]
                })
        except:
            pass
    
    return amounts

def categorize_amount(before_text, after_text, amount):
    """Try to categorize what this amount represents"""
    context = (before_text + " " + after_text).lower()
    
    categories = {
        'annual_premium': ['prime annuelle', 'prime totale', 'coût annuel', 'prime nette', 'montant annuel'],
        'building_value': ['bâtiment', 'immeuble', 'valeur du bâtiment', 'construction'],
        'insured_value': ['valeur à neuf', 'valeur assurée', 'somme assurée', 'capital assuré', 'total assuré'],
        'contents_value': ['contenu', 'mobilier', 'installations'],
        'rental_loss': ['perte de loyer', 'pertes de loyers', 'privation de jouissance', 'loyers'],
        'deductible': ['franchise', 'déductible']
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in context:
                return category
    
    return 'unknown'

# Get properties
properties = supabase.table("properties").select("id, name").execute().data
property_by_name = {p['name']: p['id'] for p in properties}

# Get existing policies
existing_policies = supabase.table("insurance_policies").select("id, property_id").execute().data
policy_by_property = {p['property_id']: p['id'] for p in existing_policies}

print(f"\n📄 Traitement de {len(proposals)} propositions...\n")

for idx, proposal_info in enumerate(proposals, 1):
    file_path = proposal_info['file']
    
    if not file_path.exists():
        print(f"\n   ❌ Fichier non trouvé: {file_path.name}")
        continue
    
    print(f"{'='*80}")
    print(f"📄 [{idx}/{len(proposals)}] {file_path.name}")
    print(f"{'='*80}")
    
    # Extract text
    print(f"   🔍 Extraction OCR...")
    text = extract_text_from_pdf(file_path)
    
    if not text:
        print(f"   ❌ Pas de texte extrait")
        continue
    
    print(f"   ✅ {len(text)} caractères extraits")
    
    # Extract all amounts
    print(f"\n   💰 Montants trouvés:")
    amounts = extract_all_amounts(text)
    
    categorized = {}
    for amt_info in amounts:
        category = categorize_amount(amt_info['before'], amt_info['after'], amt_info['amount'])
        
        # Print for debugging
        if category != 'unknown':
            print(f"      • {amt_info['amount']:>15,.2f} CHF - {category}")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(amt_info['amount'])
    
    # Build update data from categorized amounts
    update_data = {}
    
    for category, values in categorized.items():
        if category == 'deductible':
            # Use smallest for deductible
            update_data['deductible_amount'] = round(min(values), 2)
        else:
            # Use largest for values (most comprehensive)
            update_data[category] = round(max(values), 2)
    
    if update_data:
        print(f"\n   📊 Données à mettre à jour:")
        for field, value in update_data.items():
            print(f"      • {field}: {value:,.2f} CHF")
        
        # Update all properties covered by this proposal
        for prop_name in proposal_info['properties']:
            if prop_name in property_by_name:
                prop_id = property_by_name[prop_name]
                if prop_id in policy_by_property:
                    policy_id = policy_by_property[prop_id]
                    
                    try:
                        update_data['updated_at'] = datetime.now().isoformat()
                        supabase.table("insurance_policies").update(update_data).eq("id", policy_id).execute()
                        print(f"      ✅ {prop_name} mis à jour")
                    except Exception as e:
                        print(f"      ❌ Erreur {prop_name}: {str(e)}")
    
    print()

# Final report
print(f"\n{'='*80}")
print(f"  RAPPORT FINAL")
print(f"{'='*80}\n")

all_policies = supabase.table("insurance_policies").select("*").execute().data

complete_fields = {
    'policy_number': 0,
    'annual_premium': 0,
    'insured_value': 0,
    'building_value': 0,
    'rental_loss_coverage': 0,
    'deductible_amount': 0
}

total_premium = 0
total_insured = 0

for pol in all_policies:
    for field in complete_fields:
        if pol.get(field) and (isinstance(pol[field], str) or pol[field] > 0):
            complete_fields[field] += 1
    
    if pol.get('annual_premium'):
        total_premium += pol['annual_premium']
    if pol.get('insured_value'):
        total_insured += pol['insured_value']

print(f"📊 Complétude des données:")
for field, count in complete_fields.items():
    pct = (count / len(all_policies) * 100) if all_policies else 0
    print(f"   {field:25} : {count:>2}/{len(all_policies):<2} ({pct:>5.1f}%)")

if total_premium > 0:
    print(f"\n💰 TOTAUX:")
    print(f"   Primes annuelles totales : {total_premium:>15,.2f} CHF")

if total_insured > 0:
    print(f"   Valeurs assurées totales : {total_insured:>15,.0f} CHF")

print(f"\n✅ Extraction terminée!\n")



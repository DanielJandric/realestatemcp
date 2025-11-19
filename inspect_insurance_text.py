"""
Inspect insurance proposal text to understand format
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT') or os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY') or os.getenv('AZURE_FORM_RECOGNIZER_KEY')

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

document_analysis_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

# Just inspect first proposal
file_path = Path(r"Incremental1\Propositions d'assurance\PROP DU 25.01.2024-Be_Capital_SA_119567-1-601-568-342 (5).pdf")

print(f"Extraction de: {file_path.name}\n")

with open(file_path, "rb") as f:
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-document", document=f
    )
    result = poller.result()

# Extract text
full_text = ""
for page in result.pages:
    for line in page.lines:
        full_text += line.content + "\n"

print("="*80)
print("EXTRAIT DU TEXTE (premiers 3000 caractères):")
print("="*80)
print(full_text[:3000])

print("\n\n" + "="*80)
print("RECHERCHE DE MONTANTS:")
print("="*80)

# Look for lines with "CHF" or numbers
lines_with_amounts = [line for line in full_text.split('\n') if any(x in line for x in ['CHF', 'Fr.', 'francs']) or any(c.isdigit() for c in line)]

print(f"\nTrouvé {len(lines_with_amounts)} lignes avec montants/nombres:\n")

for i, line in enumerate(lines_with_amounts[:100], 1):  # First 100 lines
    if 'CHF' in line and any(c.isdigit() for c in line):
        print(f"  {i:3}. {line}")

print(f"\n✅ Terminé")


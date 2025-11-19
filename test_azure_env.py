"""
Test if Azure credentials are loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("  CHECKING AZURE CREDENTIALS")
print("="*70)

# Try different possible variable names
possible_names = [
    "AZURE_DOC_INTELLIGENCE_ENDPOINT",
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    "AZURE_FORM_RECOGNIZER_ENDPOINT",
    "AZURE_DOC_INTELLIGENCE_KEY",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "AZURE_FORM_RECOGNIZER_KEY",
]

found = {}
for name in possible_names:
    val = os.environ.get(name)
    if val:
        found[name] = val

print(f"\nFound {len(found)} Azure variables in .env:")
for key, val in found.items():
    preview = val[:30] + "..." if len(val) > 30 else val
    print(f"  {key}: {preview}")

if len(found) >= 2:
    print("\n✅ Azure credentials found!")
else:
    print("\n⚠️  Incomplete credentials")
    print("\nAll environment variables:")
    for key, val in os.environ.items():
        if 'azure' in key.lower() or 'doc' in key.lower() or 'form' in key.lower():
            preview = val[:30] + "..." if len(val) > 30 else val
            print(f"  {key}: {preview}")



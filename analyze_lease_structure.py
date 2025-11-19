"""
Analyze lease PDF structure to understand organization
"""
from pathlib import Path
from collections import defaultdict

print("="*80)
print("  ANALYZING LEASE STRUCTURE")
print("="*80)

# Find all lease PDFs
bail_patterns = [
    "**/04. Baux à loyer*/**/*bail*.pdf",
    "**/04. Baux à loyer*/**/*Bail*.pdf",
    "**/04. Baux à loyer*/**/*Bail*.PDF",
    "**/*Bail Signé*/**/*.pdf",
]

all_pdfs = []
for pattern in bail_patterns:
    pdfs = list(Path("C:/OneDriveExport").glob(pattern))
    all_pdfs.extend(pdfs)

# Filter out old leases
relevant_pdfs = [
    pdf for pdf in all_pdfs 
    if "ancien" not in str(pdf).lower() and "résili" not in str(pdf).lower()
]

print(f"\nFound {len(relevant_pdfs)} relevant lease PDFs")

# Group by parent directory
by_directory = defaultdict(list)
for pdf in relevant_pdfs:
    # Get property directory (usually 2-3 levels up)
    parts = pdf.parts
    
    # Find property directory pattern (e.g., "Gare 28 - Sion - DD")
    prop_dir = None
    for i, part in enumerate(parts):
        if " - DD" in part or part.endswith("- DD"):
            prop_dir = part
            break
        elif "Incremental1" in part and i < len(parts) - 3:
            # Check next parts
            if " - " in parts[i+1]:
                prop_dir = parts[i+1]
                break
    
    if not prop_dir:
        prop_dir = "Unknown"
    
    by_directory[prop_dir].append(pdf)

print(f"\n📁 PDFs grouped by directory:")
print(f"   {len(by_directory)} unique directories")

for dir_name, pdfs in sorted(by_directory.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{dir_name}: {len(pdfs)} PDFs")
    # Show first 3 examples
    for pdf in pdfs[:3]:
        print(f"  - {pdf.name}")
    if len(pdfs) > 3:
        print(f"  ... and {len(pdfs)-3} more")

print(f"\n{'='*80}")

# Also check "Bail Signé" directory
bail_signe = [p for p in relevant_pdfs if "Bail Signé" in str(p) or "Bail final" in str(p)]
if bail_signe:
    print(f"\n📋 Special 'Bail Signé' directory: {len(bail_signe)} PDFs")
    for pdf in bail_signe[:5]:
        print(f"  - {pdf.name}")


